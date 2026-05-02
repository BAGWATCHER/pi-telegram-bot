#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path('/home/ubuntu/pi-telegram-bot')
BOT = ROOT / 'src' / 'bot.ts'
SIDECAR = ROOT / 'src' / 'meet-sidecar.ts'

checks = []

def contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    return needle in path.read_text(encoding='utf-8', errors='ignore')

def add_check(check_id: str, ok: bool, detail: str):
    checks.append({'id': check_id, 'ok': bool(ok), 'detail': detail})

add_check('file-bot-ts', BOT.exists(), str(BOT))
add_check('file-meet-sidecar-ts', SIDECAR.exists(), str(SIDECAR))
add_check('bot-command-meet', contains(BOT, 'bot.command("meet", handleMeetCommand);'), 'meet command wired')
add_check('bot-command-meeting', contains(BOT, 'bot.command("meeting", handleMeetCommand);'), 'meeting alias wired')
add_check('bot-start-help-meet', contains(BOT, '/meet [help|setup|join|status|recover|speak|leave|doctor]'), '/start includes meet help line')
add_check('bot-state-file', contains(BOT, 'MEET_CHAT_STATE_PATH'), 'chat state persistence constant')
add_check('bot-recover-path', contains(BOT, 'meetRecoverCurrentTab'), 'recover flow integrated')

for fn in ['meetSetup', 'meetJoin', 'meetStatus', 'meetRecoverCurrentTab', 'meetLeave', 'meetSpeak', 'normalizeMeetUrlOrThrow']:
    add_check(f'sidecar-export-{fn}', contains(SIDECAR, f'export async function {fn}') or contains(SIDECAR, f'export function {fn}'), f'{fn} exported')

add_check('sidecar-launcher-fallback', contains(SIDECAR, 'npx", "-y", "openclaw"'), 'npx fallback present')
add_check('sidecar-url-validator', contains(SIDECAR, 'normalizeMeetUrlOrThrow'), 'strict URL validator present')

passed = all(c['ok'] for c in checks)
summary = {
    'project': 'chow-meet-sidecar',
    'passed': passed,
    'total_checks': len(checks),
    'passed_checks': sum(1 for c in checks if c['ok']),
    'failed_checks': [c for c in checks if not c['ok']],
    'checks': checks,
}

artifact_dir = ROOT / 'factory' / 'projects' / 'chow-meet-sidecar' / 'artifacts'
artifact_dir.mkdir(parents=True, exist_ok=True)
(artifact_dir / 'eval-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')

lines = [
    '# Chow Meet Sidecar Eval Summary',
    '',
    f"- passed: {'yes' if passed else 'no'}",
    f"- checks: {summary['passed_checks']}/{summary['total_checks']}",
    '',
    '## Checks',
]
for c in checks:
    lines.append(f"- {'✅' if c['ok'] else '❌'} {c['id']} — {c['detail']}")

(artifact_dir / 'eval-summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if passed else 1)
