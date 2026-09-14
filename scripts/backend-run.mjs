import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";

const backendDir = path.join(process.cwd(), "backend");
const venvDir = path.join(backendDir, ".venv");
const python = path.join(
  venvDir,
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
);

if (!fs.existsSync(venvDir) || !fs.existsSync(python)) {
  console.error("Backend virtual environment is missing. Run `npm run backendSetup` first.");
  process.exit(1);
}

const versionCheck = spawnSync(python, ["--version"], {
  encoding: "utf8",
  shell: false,
});

if (versionCheck.error || versionCheck.status !== 0) {
  console.error(`The virtual environment Python could not run: ${python}`);
  process.exit(1);
}

const version = (versionCheck.stdout || versionCheck.stderr).trim();
console.log(`Starting backend with ${version}`);

const server = spawn(
  python,
  [
    "-m",
    "uvicorn",
    "expose.main:app",
    "--host",
    process.env.BACKEND_HOST || "127.0.0.1",
    "--port",
    process.env.BACKEND_PORT || "8001",
    "--reload",
    "--reload-dir",
    "apis",
    "--reload-dir",
    "expose",
    "--reload-dir",
    "component",
    "--reload-dir",
    "database",
  ],
  {
    cwd: backendDir,
    env: process.env,
    stdio: "inherit",
    shell: false,
  },
);

server.on("error", (error) => {
  console.error(`Failed to start Uvicorn: ${error.message}`);
  process.exitCode = 1;
});

server.on("exit", (code, signal) => {
  process.exitCode = code ?? (signal ? 1 : 0);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.kill(signal));
}
