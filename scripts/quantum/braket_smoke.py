#!/usr/bin/env python3
"""
Amazon Braket smoke runner.
- Ensures a Braket-compatible results bucket exists (amazon-braket-<account>-us-east-1[-suffix])
- Submits a Bell-state OpenQASM task to SV1
- Polls until completion
- Prints measurement probabilities from results.json

Usage:
  python3 scripts/quantum/braket_smoke.py
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter

import boto3
from botocore.exceptions import ClientError

REGION = os.getenv("BRAKET_REGION", "us-east-1")
DEVICE_ARN = os.getenv("BRAKET_DEVICE_ARN", "arn:aws:braket:::device/quantum-simulator/amazon/sv1")
PREFIX = os.getenv("BRAKET_OUTPUT_PREFIX", "runs/smoke")
SHOTS = int(os.getenv("BRAKET_SHOTS", "100"))


def ensure_bucket(account_id: str, s3_client) -> str:
    configured = os.getenv("BRAKET_RESULTS_BUCKET", "").strip()
    if configured:
        return configured

    base = f"amazon-braket-{account_id}-{REGION}"
    bucket = base

    # If already exists and owned by us, re-use.
    try:
        s3_client.head_bucket(Bucket=bucket)
        return bucket
    except ClientError:
        pass

    # Attempt create base name, then timestamp fallback.
    try_names = [bucket, f"{base}-{int(time.time())}"]
    for name in try_names:
        try:
            if REGION == "us-east-1":
                s3_client.create_bucket(Bucket=name)
            else:
                s3_client.create_bucket(
                    Bucket=name,
                    CreateBucketConfiguration={"LocationConstraint": REGION},
                )
            s3_client.put_public_access_block(
                Bucket=name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
            return name
        except ClientError:
            continue

    raise RuntimeError("Could not create/find Braket results bucket")


def main() -> None:
    sts = boto3.client("sts")
    braket = boto3.client("braket", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)

    account_id = sts.get_caller_identity()["Account"]
    bucket = ensure_bucket(account_id, s3)

    action = {
        "braketSchemaHeader": {"name": "braket.ir.openqasm.program", "version": "1"},
        "source": (
            "OPENQASM 3.0;\n"
            "qubit[2] q;\n"
            "bit[2] b;\n"
            "h q[0];\n"
            "cnot q[0], q[1];\n"
            "b[0] = measure q[0];\n"
            "b[1] = measure q[1];"
        ),
        "inputs": {},
    }

    task = braket.create_quantum_task(
        deviceArn=DEVICE_ARN,
        shots=SHOTS,
        outputS3Bucket=bucket,
        outputS3KeyPrefix=PREFIX,
        action=json.dumps(action),
    )
    task_arn = task["quantumTaskArn"]
    print(f"Task: {task_arn}")
    print(f"Bucket: s3://{bucket}/{PREFIX}/")

    status = "QUEUED"
    task_meta = None
    for _ in range(90):
        task_meta = braket.get_quantum_task(quantumTaskArn=task_arn)
        status = task_meta["status"]
        if status in {"COMPLETED", "FAILED", "CANCELLED"}:
            break
        time.sleep(2)

    print(f"Status: {status}")
    if status != "COMPLETED":
        reason = (task_meta or {}).get("failureReason", "unknown")
        raise RuntimeError(f"Quantum task failed: {reason}")

    out_dir = task_meta["outputS3Directory"]
    key = f"{out_dir}/results.json"
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    result = json.loads(body)

    counts = Counter("".join(str(bit) for bit in m) for m in result.get("measurements", []))
    total = sum(counts.values()) or 1
    probs = {k: round(v / total, 4) for k, v in sorted(counts.items())}

    print(f"Result key: s3://{bucket}/{key}")
    print("Measurement probabilities:", json.dumps(probs, indent=2))


if __name__ == "__main__":
    main()
