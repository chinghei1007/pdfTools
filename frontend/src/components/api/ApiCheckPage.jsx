import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppShell } from "@components/layout/AppShell";
import { BodyCard } from "@components/cards/BodyCard";
import { Button } from "@components/buttons/Button";
import { Navbar } from "@components/navbar/Navbar";
import { ThemeControl } from "@components/navbar/ThemeControl";
import {
  applyEngineTheme,
  ENGINES,
  resolveThemePreference,
} from "@/theme";

const CASES = [
  {
    id: "pypdf",
    label: "pypdf operation",
    route: "/api/v1/pypdf/operations/select",
    options: { pages: "1" },
  },
  {
    id: "pymupdf",
    label: "PyMuPDF operation",
    route: "/api/v1/pymupdf/operations/rotate",
    options: { pages: "1", angle: "90" },
  },
];

async function responsePayload(response) {
  const body = await response.json().catch(() => null);
  return { status: response.status, ok: response.ok, body };
}

function createFixture(engine) {
  const text = `PDF Toolkit ${engine} API check`;
  const stream = `BT /F1 18 Tf 40 230 Td (${text}) Tj ET`;
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 420 300] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  let source = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(source.length);
    source += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xref = source.length;
  source += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  source += offsets
    .slice(1)
    .map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`)
    .join("");
  source += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return new File([source], `api-check-${engine}.pdf`, {
    type: "application/pdf",
  });
}

async function runCase(testCase) {
  const bootstrap = await responsePayload(
    await fetch("/api/v1/bootstrap", { credentials: "same-origin" }),
  );
  if (!bootstrap.ok) return { stage: "bootstrap", ...bootstrap };

  const uploadBody = new FormData();
  uploadBody.append("file", createFixture(testCase.id));
  const upload = await responsePayload(
    await fetch("/api/v1/files", {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-Toolkit-Request": "1" },
      body: uploadBody,
    }),
  );
  if (!upload.ok) return { stage: "upload", ...upload };

  const requestBody = {
    file_ids: [upload.body.id],
    options: testCase.options,
  };
  const operation = await responsePayload(
    await fetch(testCase.route, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-Toolkit-Request": "1",
      },
      body: JSON.stringify(requestBody),
    }),
  );
  const output = operation.body?.outputs?.[0];
  return {
    stage: "operation",
    request: requestBody,
    ...operation,
    passed:
      operation.ok &&
      operation.body?.job?.status === "completed" &&
      output?.available === true &&
      Boolean(output?.downloadUrl),
  };
}

function ApiCase({ testCase, state, onRun, disabled }) {
  const status = state?.status || "idle";
  return (
    <BodyCard title={testCase.label} className="pdf-api-case">
      <p className="pdf-api-case__route">POST {testCase.route}</p>
      <p
        className={`pdf-api-case__status pdf-api-case__status--${status}`}
        role="status"
      >
        {status === "running"
          ? "Running"
          : status === "success"
            ? "Success"
            : status === "failed"
              ? "Failed"
              : "Not run"}
      </p>
      <Button
        onClick={() => onRun(testCase)}
        loading={status === "running"}
        disabled={disabled}
      >
        POST test
      </Button>
      {state?.result && (
        <pre className="pdf-api-case__response">
          {JSON.stringify(state.result, null, 2)}
        </pre>
      )}
    </BodyCard>
  );
}

export function ApiCheckPage() {
  const navigate = useNavigate();
  const [theme, setTheme] = useState(
    () => localStorage.getItem("pdf-toolkit-theme") || "auto",
  );
  const [systemDark, setSystemDark] = useState(() =>
    matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const [states, setStates] = useState({});
  const busy = Object.values(states).some((state) => state.status === "running");

  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const update = (event) => setSystemDark(event.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolveThemePreference(
      theme,
      systemDark,
    );
    localStorage.setItem("pdf-toolkit-theme", theme);
    applyEngineTheme(document.documentElement, ENGINES[0]);
  }, [theme, systemDark]);

  const execute = async (testCase) => {
    setStates((previous) => ({
      ...previous,
      [testCase.id]: { status: "running" },
    }));
    try {
      const result = await runCase(testCase);
      setStates((previous) => ({
        ...previous,
        [testCase.id]: {
          status: result.passed ? "success" : "failed",
          result,
        },
      }));
    } catch (error) {
      setStates((previous) => ({
        ...previous,
        [testCase.id]: {
          status: "failed",
          result: { passed: false, error: error.message },
        },
      }));
    }
  };

  const runAll = async () => {
    for (const testCase of CASES) await execute(testCase);
  };

  return (
    <AppShell
      navbar={
        <Navbar
          brand="PDF"
          busy={busy}
          themeControl={<ThemeControl value={theme} onChange={setTheme} />}
          onAccount={() => navigate("/pypdf/render")}
          accountLabel="Back to toolkit"
        />
      }
    >
      <div className="pdf-workspace pdf-api-check">
        <header className="pdf-api-check__intro">
          <div>
            <h1 className="pdf-workspace__title">API check</h1>
            <p className="pdf-workspace__description">
              Each case creates its own one-page PDF, uploads it, posts one real
              engine operation, and validates the persisted output response.
            </p>
          </div>
          <Button onClick={runAll} loading={busy}>
            Run all POST tests
          </Button>
        </header>
        <div className="pdf-api-check__grid">
          {CASES.map((testCase) => (
            <ApiCase
              key={testCase.id}
              testCase={testCase}
              state={states[testCase.id]}
              onRun={execute}
              disabled={busy}
            />
          ))}
        </div>
      </div>
    </AppShell>
  );
}
