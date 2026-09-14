import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { execSync, spawnSync } from "node:child_process";

const ROOT = process.cwd();
const BACKEND_DIR = path.join(ROOT, "backend");
const EXPOSE_DIR = path.join(BACKEND_DIR, "expose");
const VENV_DIR = path.join(BACKEND_DIR, ".venv");
const REQUIREMENTS_TXT = path.join(BACKEND_DIR, "requirements.txt");
const HASH_FILE = path.join(VENV_DIR, ".requirements-hash");
const MIN_PYTHON = [3, 10];

function run(cmd, options = {}) {
  execSync(cmd, {
    stdio: "inherit",
    shell: true,
    ...options,
  });
}

function runOutput(cmd, options = {}) {
  return execSync(cmd, {
    encoding: "utf8",
    shell: true,
    stdio: ["pipe", "pipe", "pipe"],
    ...options,
  }).toString().trim();
}

function parseVersion(output) {
  const match = /Python\\s+(\\d+)\\.(\\d+)\\.(\\d+)/.exec(output || "");
  if (!match) return null;
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    raw: match[0],
  };
}

function isVersionOk(version) {
  if (!version) return false;
  return (
    version.major > MIN_PYTHON[0] ||
    (version.major === MIN_PYTHON[0] && version.minor >= MIN_PYTHON[1])
  );
}

function findPython() {
  const candidates = [
    { command: "python", args: ["-V"] },
    { command: "python3", args: ["-V"] },
  ];

  for (const c of candidates) {
    try {
      const result = runOutput(`${c.command} ${c.args[0]}`);
      const version = parseVersion(result);
      if (isVersionOk(version)) {
        return { command: c.command, version };
      }
    } catch {
      // Keep trying candidates.
    }
  }

  try {
    const result = runOutput("py -3 -V");
    const version = parseVersion(result);
    if (isVersionOk(version)) {
      return { command: "py", args: ["-3"], version };
    }
  } catch {
    // Continue below.
  }

  throw new Error(`Need Python >= ${MIN_PYTHON.join(".")} in PATH`);
}

function pythonCommand(python) {
  return [python.command, ...(python.args || [])].join(" ").trim();
}

function fileHash(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath, "utf8"), "utf8").digest("hex");
}

function pythonInVenv() {
  return process.platform === "win32"
    ? path.join(VENV_DIR, "Scripts", "python.exe")
    : path.join(VENV_DIR, "bin", "python");
}

function setupBackendDeps() {
  if (!fs.existsSync(BACKEND_DIR)) {
    throw new Error(`Missing backend folder: ${BACKEND_DIR}`);
  }

  if (!fs.existsSync(EXPOSE_DIR)) {
    throw new Error(`Missing backend/expose folder: ${EXPOSE_DIR}`);
  }

  if (!fs.existsSync(REQUIREMENTS_TXT)) {
    throw new Error(`Missing backend/requirements.txt`);
  }

  const python = findPython();
  const pyCmd = pythonCommand(python);
  console.log(`Using ${python.version.raw}`);

  if (!fs.existsSync(VENV_DIR)) {
    run(`${pyCmd} -m venv \"${VENV_DIR}\"`);
    console.log(`Created virtualenv: ${VENV_DIR}`);
  } else {
    console.log(`Using existing virtualenv: ${VENV_DIR}`);
  }

  const py = pythonInVenv();
  run(`\"${py}\" -m pip install --upgrade pip`, { cwd: BACKEND_DIR });

  const nextHash = fileHash(REQUIREMENTS_TXT);
  const prevHash = fs.existsSync(HASH_FILE) ? fs.readFileSync(HASH_FILE, "utf8") : "";

  if (nextHash !== prevHash) {
    run(`\"${py}\" -m pip install -r \"${REQUIREMENTS_TXT}\"`, { cwd: BACKEND_DIR });
    fs.writeFileSync(HASH_FILE, nextHash, "utf8");
  } else {
    console.log("requirements.txt unchanged; skipping pip install.");
  }

  return py;
}

function startServer() {
  const py = setupBackendDeps();

  const host = process.env.BACKEND_HOST || "0.0.0.0";
  const port = process.env.BACKEND_PORT || "8000";

  const result = spawnSync(
    `"${py}"`,
    ["-m", "uvicorn", "main:app", "--host", host, "--port", String(port), "--reload"],
    {
      stdio: "inherit",
      shell: true,
      cwd: EXPOSE_DIR,
      env: {
        ...process.env,
        PYTHONPATH: `${BACKEND_DIR}${path.delimiter}${process.env.PYTHONPATH || ""}`,
      },
    }
  );

  process.exit(result.status ?? 1);
}

startServer();
