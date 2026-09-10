import { execSync, spawnSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const BACKEND_DIR = path.join(process.cwd(), "backend");
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

function sh(cmd) {
  return execSync(cmd, {
    encoding: "utf8",
    shell: true,
    stdio: ["pipe", "pipe", "pipe"],
  });
}

function parseVersion(output) {
  const match = /Python\s+(\d+)\.(\d+)\.(\d+)/.exec(output || "");
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
    { command: "py", args: ["-3"] },
    { command: "python3", args: [] },
    { command: "python", args: [] },
  ];

  for (const c of candidates) {
    try {
      const proc = spawnSync(c.command, [...c.args, "--version"], {
        encoding: "utf8",
        shell: false,
      });
      const text = (proc.stdout || proc.stderr || "").toString();
      const version = parseVersion(text);
      if (!proc.error && isVersionOk(version)) {
        return { ...c, version };
      }
    } catch {
      // Continue trying.
    }
  }
  throw new Error(`Need Python >= ${MIN_PYTHON.join(".")} in PATH`);
}

function pythonCommand(python) {
  return [python.command, ...python.args].join(" ").trim();
}

function fileHash(filePath) {
  return crypto
    .createHash("sha256")
    .update(fs.readFileSync(filePath, "utf8"), "utf8")
    .digest("hex");
}

function setup() {
  if (!fs.existsSync(BACKEND_DIR)) {
    throw new Error(`Missing backend folder: ${BACKEND_DIR}`);
  }

  if (!fs.existsSync(REQUIREMENTS_TXT)) {
    throw new Error(`Missing backend/requirements.txt`);
  }

  const python = findPython();
  const pyCmd = pythonCommand(python);
  console.log(`Using ${python.version.raw}`);

  if (!fs.existsSync(VENV_DIR)) {
    run(`${pyCmd} -m venv "${VENV_DIR}"`);
    console.log(`Created virtualenv: ${VENV_DIR}`);
  } else {
    console.log(`Using existing virtualenv: ${VENV_DIR}`);
  }

  const pythonInVenv = process.platform === "win32"
    ? path.join(VENV_DIR, "Scripts", "python.exe")
    : path.join(VENV_DIR, "bin", "python");

  run(`"${pythonInVenv}" -m pip install --upgrade pip`, { cwd: BACKEND_DIR });

  const nextHash = fileHash(REQUIREMENTS_TXT);
  const prevHash = fs.existsSync(HASH_FILE) ? fs.readFileSync(HASH_FILE, "utf8") : "";

  if (nextHash !== prevHash) {
    run(`"${pythonInVenv}" -m pip install -r "${REQUIREMENTS_TXT}"`, { cwd: BACKEND_DIR });
    fs.writeFileSync(HASH_FILE, nextHash, "utf8");
  } else {
    console.log("requirements.txt unchanged; skip pip install.");
  }

  run(`"${pythonInVenv}" -m playwright install chromium`, { cwd: BACKEND_DIR });

  const tesseractCheck = spawnSync("tesseract", ["--version"], {
    encoding: "utf8",
    shell: true,
  });
  if (tesseractCheck.status === 0) {
    console.log("✅ tesseract detected.");
  } else {
    console.warn("⚠️  tesseract not found in PATH; OCR service may fail.");
  }

  const finalPy = sh(`"${pythonInVenv}" --version`).toString().trim();
  console.log(`Backend setup done. ${finalPy}`);
  console.log(
    `Activate command: ${
      process.platform === "win32"
        ? "backend\\\\.venv\\\\Scripts\\\\activate"
        : "source backend/.venv/bin/activate"
    }`
  );
}

setup();
