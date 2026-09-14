import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  ApiCheckPage, AppShell, BodyCard, Button, EngineSwitch, FileCollection, FileDropzone,
  HistoryDialog, Input, Navbar, ProcessingStatus, ResultPanel, Select,
  Sidebar, ThemeControl,
} from "@components";
import { downloadFile, request } from "@components/pymupdf/api";
import { applyEngineTheme, ENGINES, resolveThemePreference } from "@/theme";

const BUSY_STATES = new Set(["uploading", "previewing", "running", "downloading"]);

function defaults(tool) {
  return Object.fromEntries((tool?.fields || []).map((field) => [field.key, field.default ?? ""]));
}

function uniqueTools(tools) {
  const seen = new Set();
  return tools.filter((tool) => !seen.has(tool.id) && seen.add(tool.id));
}

function Toolkit() {
  const { engineId, toolId } = useParams();
  const navigate = useNavigate();
  const engine = ENGINES.find((item) => item.id === engineId) || ENGINES[0];
  const [catalogs, setCatalogs] = useState({ pypdf: [], pymupdf: [] });
  const [files, setFiles] = useState([]);
  const [options, setOptions] = useState({});
  const [password, setPassword] = useState("");
  const [workflow, setWorkflow] = useState("idle");
  const [progress, setProgress] = useState(undefined);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [pages, setPages] = useState([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyEntries, setHistoryEntries] = useState([]);
  const [historyCursor, setHistoryCursor] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyEngine, setHistoryEngine] = useState("");
  const [historyTool, setHistoryTool] = useState("");
  const [theme, setTheme] = useState(() => localStorage.getItem("pdf-toolkit-theme") || "auto");
  const [systemDark, setSystemDark] = useState(() => matchMedia("(prefers-color-scheme: dark)").matches);
  const resolvedTheme = resolveThemePreference(theme, systemDark);
  const activeRoute = useRef("");
  const lastTools = useRef({ pypdf: "render", pymupdf: "render" });
  const resultRef = useRef(null);
  const tool = catalogs[engine.id]?.find((item) => item.id === toolId);
  const busy = BUSY_STATES.has(workflow);

  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const update = (event) => setSystemDark(event.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme;
    localStorage.setItem("pdf-toolkit-theme", theme);
  }, [theme, resolvedTheme]);

  useEffect(() => {
    applyEngineTheme(document.documentElement, engine);
  }, [engine, resolvedTheme]);

  useEffect(() => {
    const controller = new AbortController();
    request("/bootstrap", undefined, controller.signal)
      .then(() => Promise.all(ENGINES.map(({ id }) => request(`/${id}/tools`, undefined, controller.signal))))
      .then(([pypdf, pymupdf]) => setCatalogs({ pypdf, pymupdf }))
      .catch((failure) => failure.name !== "AbortError" && setError(failure.message));
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const tools = catalogs[engine.id];
    if (!tools.length) return;
    if (!tool) {
      navigate(`/${engine.id}/${tools[0].id}`, { replace: true });
      return;
    }
    const route = `${engine.id}/${tool.id}`;
    lastTools.current[engine.id] = tool.id;
    if (activeRoute.current !== route) {
      activeRoute.current = route;
      setFiles([]);
      setOptions(defaults(tool));
      setPassword("");
      setResult(null);
      setPages([]);
      setError("");
      setWorkflow("idle");
    }
  }, [catalogs, engine.id, navigate, tool]);

  useEffect(() => {
    if (workflow !== "succeeded" || !result) return;
    requestAnimationFrame(() => {
      const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
      resultRef.current?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
      resultRef.current?.focus({ preventScroll: true });
    });
  }, [workflow, result]);

  useEffect(() => {
    if (!historyOpen) return;
    const controller = new AbortController();
    // Synchronize the controlled dialog with its remote collection.
    // oxlint-disable-next-line react/set-state-in-effect
    setHistoryLoading(true);
    // oxlint-disable-next-line react/set-state-in-effect
    setHistoryError("");
    const query = new URLSearchParams({ limit: "50" });
    if (historyEngine) query.set("engine", historyEngine);
    if (historyTool) query.set("tool_id", historyTool);
    request(`/history?${query}`, undefined, controller.signal)
      .then(({ entries, nextCursor }) => {
        setHistoryEntries(entries);
        setHistoryCursor(nextCursor);
      })
      .catch((failure) => failure.name !== "AbortError" && setHistoryError(failure.message))
      .finally(() => setHistoryLoading(false));
    return () => controller.abort();
  }, [historyOpen, historyEngine, historyTool]);

  const categories = useMemo(() => [...new Set((catalogs[engine.id] || []).map((item) => item.category))].map((label) => ({ id: label, label, disabled: busy })), [catalogs, engine.id, busy]);
  const category = tool?.category || categories[0]?.id || "Tools";
  const historyTools = useMemo(() => uniqueTools(historyEngine ? catalogs[historyEngine] || [] : [...catalogs.pypdf, ...catalogs.pymupdf]), [catalogs, historyEngine]);
  const labeledHistory = useMemo(() => historyEntries.map((entry) => ({
    ...entry,
    toolLabel: catalogs[entry.engine]?.find((item) => item.id === entry.toolId)?.label || entry.toolId,
  })), [historyEntries, catalogs]);

  const changeTool = (id) => {
    if (busy) return;
    activeRoute.current = "";
    navigate(`/${engine.id}/${id}`);
  };

  const upload = async (selectedFiles) => {
    if (!tool || busy) return;
    setError(""); setResult(null); setPages([]); setWorkflow("uploading");
    const existing = tool.multiple ? files : [];
    if (existing.length + selectedFiles.length > 10) {
      setWorkflow("failed"); setError("Maximum 10 input files."); return;
    }
    setFiles(existing);
    try {
      const added = [];
      for (let index = 0; index < selectedFiles.length; index += 1) {
        const body = new FormData();
        body.append("file", selectedFiles[index]);
        body.append("password", password);
        setMessage(`Uploading ${index + 1} of ${selectedFiles.length}`);
        setProgress(Math.round((index / selectedFiles.length) * 100));
        const saved = await request("/files", body);
        const entry = { ...saved, password };
        if (saved.mediaType?.startsWith("image/")) entry.url = `/api/v1/files/${saved.id}/download`;
        added.push(entry);
        setFiles([...existing, ...added]);
        if (saved.mediaType === "application/pdf") {
          setWorkflow("previewing");
          setMessage(`Generating preview ${index + 1} of ${selectedFiles.length}`);
          try {
            const preview = await request(`/files/${saved.id}/preview`, { page: 1, password });
            entry.url = preview.url; entry.mediaType = "image/png"; entry.sourceMediaType = saved.mediaType;
            setFiles([...existing, ...added]);
          } catch (previewError) {
            entry.error = `Preview unavailable: ${previewError.message}`;
          }
          setWorkflow("uploading");
        }
      }
      setProgress(100); setMessage(""); setWorkflow("ready");
    } catch (failure) {
      setError(failure.message); setWorkflow("failed"); setProgress(undefined);
    }
  };

  const run = async () => {
    if (!tool || busy) return;
    setError(""); setMessage(`Running ${tool.label}…`); setProgress(undefined); setWorkflow("running"); setResult(null);
    try {
      const response = await request(`/${engine.id}/operations/${tool.id}`, {
        file_ids: files.map((file) => file.id),
        options,
        passwords: Object.fromEntries(files.filter((file) => file.password).map((file) => [file.id, file.password])),
      });
      setResult({
        ...response,
        outputs: response.outputs.map((output) => ({
          ...output,
          url: output.mediaType?.startsWith("image/") ? output.downloadUrl : output.url,
        })),
      });
      setMessage("Processing complete."); setWorkflow("succeeded");
    } catch (failure) {
      setError(failure.message); setMessage(""); setWorkflow("failed");
    }
  };

  const download = async (entry) => {
    if (entry.available === false) return;
    setError(""); setMessage(`Downloading ${entry.name}…`); setWorkflow("downloading");
    try { await downloadFile(entry); setMessage("Download started."); setWorkflow("succeeded"); }
    catch (failure) { setError(failure.message); setWorkflow("failed"); }
  };

  const restoreHistory = async (entry) => {
    if (busy) return;
    setHistoryLoading(true); setHistoryError("");
    try {
      const detail = await request(`/history/${entry.id}`);
      const targetTool = catalogs[detail.engine]?.find((item) => item.id === detail.toolId);
      if (!targetTool) throw new Error("This history tool is no longer available.");
      activeRoute.current = `${detail.engine}/${detail.toolId}`;
      setFiles((detail.inputs || []).filter(Boolean).map((file) => ({ ...file, sourceMediaType: file.mediaType })));
      setOptions({ ...defaults(targetTool), ...detail.options });
      setPassword(""); setPages([]); setError("");
      setResult({
        job: detail,
        outputs: (detail.outputs || []).filter(Boolean).map((output) => ({
          ...output,
          url: output.mediaType?.startsWith("image/") ? output.downloadUrl : output.url,
        })),
      });
      setHistoryOpen(false); setWorkflow("succeeded");
      navigate(`/${detail.engine}/${detail.toolId}`);
    } catch (failure) { setHistoryError(failure.message); }
    finally { setHistoryLoading(false); }
  };

  const loadMoreHistory = async () => {
    if (!historyCursor) return;
    setHistoryLoading(true);
    const query = new URLSearchParams({ limit: "50", cursor: historyCursor });
    if (historyEngine) query.set("engine", historyEngine);
    if (historyTool) query.set("tool_id", historyTool);
    try {
      const response = await request(`/history?${query}`);
      setHistoryEntries((previous) => [...previous, ...response.entries]);
      setHistoryCursor(response.nextCursor);
    } catch (failure) { setHistoryError(failure.message); }
    finally { setHistoryLoading(false); }
  };

  const loadPages = async () => {
    const file = files[0];
    if (!file || file.pages > 30) { setError("Page thumbnails are limited to PDFs with 30 pages or fewer."); return; }
    setWorkflow("previewing"); setError(""); setPages([]);
    try {
      const loaded = [];
      for (let page = 1; page <= file.pages; page += 1) {
        setMessage(`Loading page ${page} of ${file.pages}`); setProgress(Math.round(((page - 1) / file.pages) * 100));
        const preview = await request(`/files/${file.id}/preview`, { page, password: file.password || "" });
        loaded.push({ page, url: preview.url }); setPages([...loaded]);
      }
      setOptions((previous) => ({ ...previous, pages: loaded.map((item) => item.page).join(",") }));
      setProgress(100); setMessage(""); setWorkflow("ready");
    } catch (failure) { setError(failure.message); setWorkflow("failed"); }
  };

  const movePage = (from, to) => {
    const next = [...pages]; const [page] = next.splice(from, 1); next.splice(to, 0, page);
    setPages(next); setOptions((previous) => ({ ...previous, pages: next.map((item) => item.page).join(",") }));
  };

  if (!ENGINES.some((item) => item.id === engineId)) return <Navigate to="/pypdf/render" replace />;

  const canRun = Boolean(tool) && (tool.id === "html-to-pdf" ? files.length === 1 || String(options.html || "").trim() : files.length > 0);
  const statusName = busy ? "running" : workflow === "failed" ? "failed" : workflow === "succeeded" ? "succeeded" : "idle";

  return (
    <AppShell
      navbar={
        <Navbar
          brand="PDF"
          categories={categories}
          categoryId={category}
          busy={busy}
          onCategoryChange={(id) => changeTool(catalogs[engine.id].find((item) => item.category === id)?.id)}
          onHistory={() => setHistoryOpen(true)}
          engineSwitch={
            <EngineSwitch
              engines={ENGINES}
              value={engine.id}
              disabled={busy}
              onChange={(id) => {
                activeRoute.current = "";
                navigate(`/${id}/${lastTools.current[id]}`);
              }}
            />
          }
          themeControl={<ThemeControl value={theme} onChange={setTheme} />}
          onAccount={() => navigate("/api-check")}
          accountLabel="API check"
        />
      }
      sidebar={<Sidebar title={category} items={(catalogs[engine.id] || []).filter((item) => item.category === category).map((item) => ({ ...item, disabled: busy }))} selectedId={tool?.id} onSelect={changeTool} />}
      overlays={<HistoryDialog open={historyOpen} onClose={() => setHistoryOpen(false)} entries={labeledHistory} loading={historyLoading} error={historyError} onSelect={restoreHistory} engine={historyEngine} toolId={historyTool} tools={historyTools} onEngineChange={(value) => { setHistoryEngine(value); setHistoryTool(""); }} onToolChange={setHistoryTool} onLoadMore={loadMoreHistory} hasMore={Boolean(historyCursor)} selectionDisabled={busy} />}
    >
      <div className="pdf-workspace">
        <header>
          <h1 className="pdf-workspace__title">{tool?.label || "Connecting to PDF services"}</h1>
          <p className="pdf-workspace__description">Local document processing with {engine.label}. Originals are preserved and History stays on this computer.</p>
          {tool?.engine && tool.engine.toLowerCase() !== engine.id && <span className="pdf-assistance-badge">{tool.engine}-assisted</span>}
        </header>
        {error && <p role="alert" className="pdf-error">{error}</p>}
        {tool && <>
          <BodyCard title="Input files">
            <div className="pdf-workspace">
              {tool.input === "pdf" && <Input label="Input PDF password (only if encrypted)" type="password" value={password} disabled={busy} onChange={(event) => setPassword(event.target.value)} />}
              <FileDropzone key={`${engine.id}-${tool.id}`} type={tool.input} multiple={tool.multiple} disabled={busy} maxSizeBytes={20 * 1024 * 1024} onFilesSelected={upload} label={tool.id === "html-to-pdf" ? "Drop an HTML file here" : "Drop files here"} />
              <FileCollection files={files} onRemove={busy ? undefined : (id) => { setFiles((previous) => previous.filter((file) => file.id !== id)); setResult(null); setPages([]); }} onReorder={busy || !tool.multiple ? undefined : (from, to) => setFiles((previous) => { const next = [...previous]; const [file] = next.splice(from, 1); next.splice(to, 0, file); return next; })} />
            </div>
          </BodyCard>
          <BodyCard title="Settings">
            <fieldset className="pdf-settings" disabled={busy}>
              <legend>Tool options</legend>
              {tool.fields.map((field) => field.kind === "select" ? <Select key={field.key} label={field.label} value={options[field.key] ?? field.default} options={field.choices.map((value) => ({ value, label: value }))} onChange={(event) => setOptions({ ...options, [field.key]: event.target.value })} /> : field.kind === "checkbox" ? <label key={field.key} className="pdf-checkbox"><input type="checkbox" checked={Boolean(options[field.key])} onChange={(event) => setOptions({ ...options, [field.key]: event.target.checked })} />{field.label}</label> : field.kind === "textarea" ? <label key={field.key} className="pdf-field"><span className="pdf-field__label">{field.label}</span><textarea className="pdf-field__control" value={options[field.key] ?? field.default} onChange={(event) => setOptions({ ...options, [field.key]: event.target.value })} /></label> : <Input key={field.key} label={field.label} type={field.kind || "text"} min={field.min} max={field.max} value={options[field.key] ?? field.default} onChange={(event) => setOptions({ ...options, [field.key]: event.target.value })} />)}
              {!tool.fields.length && <p className="pdf-muted">No additional settings for this operation.</p>}
            </fieldset>
          </BodyCard>
          {tool.id === "select" && <BodyCard title="Individual page order"><Button variant="secondary" disabled={busy || files.length !== 1} onClick={loadPages}>Load page thumbnails</Button><div className="pdf-page-grid">{pages.map((page, index) => <article className="pdf-page" key={`${page.page}-${index}`}><img src={page.url} alt={`Page ${page.page}`} /><strong>Page {page.page}</strong><div><Button size="sm" variant="secondary" disabled={busy || index === 0} onClick={() => movePage(index, index - 1)}>Earlier</Button><Button size="sm" variant="secondary" disabled={busy || index === pages.length - 1} onClick={() => movePage(index, index + 1)}>Later</Button></div></article>)}</div></BodyCard>}
          <div className="pdf-workspace__actions">
            <Button size="lg" loading={workflow === "running"} disabled={busy || !canRun} onClick={run}>Run {tool.label}</Button>
            <ProcessingStatus status={statusName} progress={progress} message={message || undefined} />
          </div>
        </>}
        {result && <section id="result" ref={resultRef} tabIndex={-1} aria-label="Processing result"><ResultPanel files={result.outputs} onDownload={download} onReset={() => { setResult(null); setWorkflow(files.length ? "ready" : "idle"); }}><p className="pdf-muted">Job {result.job.id}</p></ResultPanel></section>}
      </div>
    </AppShell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/pypdf/render" replace />} />
      <Route path="/api-check" element={<ApiCheckPage />} />
      <Route path="/:engineId/:toolId" element={<Toolkit />} />
      <Route path="*" element={<Navigate to="/pypdf/render" replace />} />
    </Routes>
  );
}
