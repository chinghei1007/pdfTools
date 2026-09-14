import { spawn } from "node:child_process";
import path from "node:path";
import process from "node:process";

const ROOT = process.cwd();
const children = new Map();

function start(name, command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: ROOT,
    stdio: "inherit",
    shell: true,
    ...options,
  });

  children.set(name, child);

  child.on("error", (error) => {
    console.error(`[${name}] failed to start:`, error.message);
    shutdown(1);
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      console.log(`[${name}] exited with signal ${signal}`);
    } else {
      console.log(`[${name}] exited with code ${code}`);
    }
    shutdown(code ?? 0);
  });

  return child;
}

function shutdown(code = 0) {
  for (const [name, child] of children.entries()) {
    if (!child.killed) {
      child.kill("SIGINT");
    }
  }
  if (code !== 0) {
    process.exitCode = code;
  }
}

start("backend", "npm", ["run", "backend"], { cwd: ROOT });
start("frontend", "npm", ["run", "dev"], { cwd: path.join(ROOT, "frontend") });

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
