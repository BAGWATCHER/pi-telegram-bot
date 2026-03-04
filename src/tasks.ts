import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

const BOT_ROOT = process.cwd();
const TASKS_FILE = path.join(BOT_ROOT, "tasks.json");
const TASKS_DIR = path.join(BOT_ROOT, "task-outputs");

export interface Task {
  id: string;
  chatId: number;
  project: string;
  projectPath: string;
  description: string;
  tmuxSession: string;
  status: "running" | "done" | "failed" | "cancelled";
  startedAt: string;
  finishedAt?: string;
  summary?: string;
}

function loadTasks(): Task[] {
  try {
    if (!fs.existsSync(TASKS_FILE)) return [];
    return JSON.parse(fs.readFileSync(TASKS_FILE, "utf8"));
  } catch {
    return [];
  }
}

function saveTasks(tasks: Task[]): void {
  fs.writeFileSync(TASKS_FILE, JSON.stringify(tasks, null, 2));
}

export function createTask(task: Omit<Task, "id" | "startedAt" | "status">): Task {
  fs.mkdirSync(TASKS_DIR, { recursive: true });
  const tasks = loadTasks();
  const id = `t${Date.now().toString(36)}`;
  const newTask: Task = {
    ...task,
    id,
    status: "running",
    startedAt: new Date().toISOString(),
  };
  tasks.push(newTask);
  saveTasks(tasks);
  return newTask;
}

export function updateTask(id: string, update: Partial<Task>): void {
  const tasks = loadTasks();
  const idx = tasks.findIndex((t) => t.id === id);
  if (idx === -1) return;
  tasks[idx] = { ...tasks[idx], ...update };
  saveTasks(tasks);
}

export function getTask(id: string): Task | undefined {
  return loadTasks().find((t) => t.id === id);
}

export function listTasks(status?: Task["status"]): Task[] {
  const tasks = loadTasks();
  if (!status) return tasks;
  return tasks.filter((t) => t.status === status);
}

export function getOutputPath(taskId: string): string {
  return path.join(TASKS_DIR, `${taskId}.md`);
}

export function writeOutput(taskId: string, content: string): void {
  fs.mkdirSync(TASKS_DIR, { recursive: true });
  fs.writeFileSync(getOutputPath(taskId), content);
}

export function readOutput(taskId: string): string | null {
  const p = getOutputPath(taskId);
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p, "utf8");
}
