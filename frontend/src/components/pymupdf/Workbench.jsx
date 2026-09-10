import { useEffect, useRef, useState } from "react";
import {
  AppShell,
  Navbar,
  Sidebar,
  BodyCard,
  Button,
  Input,
  Select,
  FileDropzone,
  FileCollection,
  ProcessingStatus,
} from "@components";
import { request } from "@components/pymupdf/api";
import { logUploadEvent } from "@components/upload/events";

export default function Workbench() {
  const [tools, setTools] = useState([]);
  const [selected, setSelected] = useState("render");
  const [files, setFiles] = useState([]);
  const [options, setOptions] = useState({});
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [pages, setPages] = useState([]);
  const [catalog, setCatalog] = useState(null);
  const [query, setQuery] = useState("");
  const pending = useRef(false);
  const tool = tools.find((item) => item.id === selected);
  useEffect(() => {
    const abort = new AbortController();
    request("/tools", undefined, abort.signal)
      .then((items) => {
        setTools(items);
        setOptions(
          Object.fromEntries(
            items
              .find((item) => item.id === "render")
              .fields.map((f) => [f.key, f.default]),
          ),
        );
      })
      .catch((failure) => {
        if (failure.name !== "AbortError") setError(failure.message);
      });
    return () => abort.abort();
  }, []);
  const choose = (id) => {
    if (pending.current) return;
    setSelected(id);
    setFiles([]);
    setPages([]);
    setResult(null);
    setError("");
    setPassword("");
    setOptions(
      Object.fromEntries(
        tools
          .find((item) => item.id === id)
          .fields.map((field) => [field.key, field.default]),
      ),
    );
  };
  const execute = async (action) => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (failure) {
      setError(failure.message);
      logUploadEvent("request.failed");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };
  const upload = (selectedFiles) =>
    execute(async () => {
      if ((tool.multiple ? files.length : 0) + selectedFiles.length > 10)
        throw new Error("Maximum 10 input files.");
      setResult(null);
      setPages([]);
      if (!tool.multiple) setFiles([]);
      for (const file of selectedFiles) {
        const body = new FormData();
        body.append("file", file);
        body.append("password", password);
        logUploadEvent("upload.started");
        const saved = await request("/files", body);
        if (saved.persisted) logUploadEvent("file.db_save.succeeded");
        // Keep credentials in memory only; never include them in console events.
        const entry = { ...saved, sourceMediaType: saved.mediaType, password };
        setFiles((previous) => [...previous, entry]);
        try {
          const preview = await request(`/files/${saved.id}/preview`, {
            page: 1,
            password,
          });
          logUploadEvent("preview.ready", { page: 1, cached: preview.cached });
          setFiles((previous) =>
            previous.map((item) =>
              item.id === saved.id
                ? { ...item, url: preview.url, mediaType: "image/png" }
                : item,
            ),
          );
        } catch (failure) {
          setFiles((previous) =>
            previous.map((item) =>
              item.id === saved.id
                ? { ...item, error: `Preview unavailable: ${failure.message}` }
                : item,
            ),
          );
          logUploadEvent("preview.failed");
        }
      }
    });
  const loadPages = () =>
    execute(async () => {
      const file = files[0];
      if (file.pages > 30)
        throw new Error(
          "Page grid is limited to 30 pages. Use the page-number setting for larger PDFs.",
        );
      const items = [];
      for (let page = 1; page <= file.pages; page++) {
        const preview = await request(`/files/${file.id}/preview`, {
          page,
          password: file.password,
        });
        items.push({ page, url: preview.url });
      }
      setPages(items);
      setOptions((previous) => ({
        ...previous,
        pages: items.map((p) => p.page).join(","),
      }));
    });
  const movePage = (from, to) => {
    const next = [...pages];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    setPages(next);
    setOptions((previous) => ({
      ...previous,
      pages: next.map((p) => p.page).join(","),
    }));
  };
  const run = () =>
    execute(async () => {
      setResult(null);
      const output = await request(`/operations/${tool.id}`, {
        file_ids: files.map((f) => f.id),
        options,
        passwords: Object.fromEntries(files.map((f) => [f.id, f.password])),
      });
      setResult(output);
      logUploadEvent("operation.succeeded");
    });
  const category = tool?.category || "Convert";
  const categories = [...new Set(tools.map((item) => item.category))].map(
    (label) => ({ id: label, label, disabled: busy }),
  );
  return (
    <AppShell
      navbar={
        <Navbar
          brand="PyMuPDF Workbench · V1"
          categories={categories}
          categoryId={category}
          onCategoryChange={(id) =>
            choose(tools.find((item) => item.category === id).id)
          }
        />
      }
      sidebar={
        <Sidebar
          title={category}
          items={tools
            .filter((item) => item.category === category)
            .map((item) => ({ ...item, disabled: busy }))}
          selectedId={selected}
          onSelect={choose}
        />
      }
    >
      <div className="mx-auto flex max-w-5xl flex-col gap-5">
        <BodyCard
          title={tool?.label || "Connecting to the service"}
          description="Local document processing. Uploads are saved on this computer; originals are preserved. Select a category from Menu."
        >
          {error && (
            <p role="alert" className="text-red-700">
              {error}
            </p>
          )}
          {busy && <ProcessingStatus status="running" message="Working…" />}
          {!tools.length && (
            <Button onClick={() => window.location.reload()}>Reconnect</Button>
          )}
        </BodyCard>
        {tool && (
          <>
            <BodyCard title="Input files">
              <div className="flex flex-col gap-4">
                {tool.input === "pdf" && (
                  <Input
                    label="Input PDF password (only if encrypted)"
                    type="password"
                    value={password}
                    disabled={busy}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                )}
                <FileDropzone
                  key={tool.id}
                  type={tool.input}
                  multiple={tool.multiple}
                  disabled={busy}
                  maxSizeBytes={20 * 1024 * 1024}
                  onFilesSelected={upload}
                />
                <FileCollection
                  files={files}
                  onRemove={
                    busy
                      ? undefined
                      : (id) => {
                          setFiles(files.filter((f) => f.id !== id));
                          setPages([]);
                          setResult(null);
                        }
                  }
                  onReorder={
                    busy || !tool.multiple
                      ? undefined
                      : (from, to) => {
                          const next = [...files];
                          const [f] = next.splice(from, 1);
                          next.splice(to, 0, f);
                          setFiles(next);
                          setResult(null);
                        }
                  }
                />
              </div>
            </BodyCard>
            <BodyCard title="Settings">
              <div className="flex flex-col gap-4">
                {tool.fields.map((field) =>
                  field.kind === "select" ? (
                    <Select
                      key={field.key}
                      label={field.label}
                      disabled={busy}
                      value={options[field.key] ?? field.default}
                      options={field.choices.map((value) => ({
                        value,
                        label: value,
                      }))}
                      onChange={(event) => {
                        setResult(null);
                        setOptions({
                          ...options,
                          [field.key]: event.target.value,
                        });
                      }}
                    />
                  ) : (
                    <Input
                      key={field.key}
                      label={field.label}
                      disabled={busy}
                      type={field.kind}
                      value={options[field.key] ?? field.default}
                      onChange={(event) => {
                        setResult(null);
                        if (field.key === "pages") setPages([]);
                        setOptions({
                          ...options,
                          [field.key]: event.target.value,
                        });
                      }}
                    />
                  ),
                )}
                {!tool.fields.length && (
                  <p className="text-sm text-slate-600">
                    No additional settings for this operation.
                  </p>
                )}
              </div>
            </BodyCard>
            {selected === "select" && files.length === 1 && (
              <BodyCard title="Individual page order">
                <Button disabled={busy} onClick={loadPages}>
                  Load page thumbnails
                </Button>
                <div className="mt-4 grid gap-3 sm:grid-cols-3">
                  {pages.map((page, index) => (
                    <div key={page.page}>
                      <img
                        loading="lazy"
                        className="h-40 w-full object-contain"
                        src={page.url}
                        alt={`Page ${page.page}`}
                      />
                      <p>Page {page.page}</p>
                      <Button
                        size="sm"
                        disabled={busy || index === 0}
                        onClick={() => movePage(index, index - 1)}
                      >
                        Earlier
                      </Button>
                      <Button
                        size="sm"
                        disabled={busy || index === pages.length - 1}
                        onClick={() => movePage(index, index + 1)}
                      >
                        Later
                      </Button>
                    </div>
                  ))}
                </div>
              </BodyCard>
            )}
            <Button disabled={busy || !files.length} onClick={run}>
              Run {tool.label}
            </Button>
          </>
        )}
        {result && (
          <BodyCard title="Result">
            <p>
              {result.name} · {Math.round(result.size / 1024)} KB
            </p>
            <a href={result.downloadUrl} className="text-blue-700 underline">
              Download result
            </a>
          </BodyCard>
        )}
        <BodyCard
          title="PyMuPDF API reference"
          description="Full public symbol inventory for the installed version. This reference includes low-level APIs; only the document operations in Menu are executable through HTTP."
        >
          <Button
            variant="secondary"
            disabled={busy}
            onClick={() =>
              execute(async () => setCatalog(await request("/catalog")))
            }
          >
            Load API catalogue
          </Button>
          {catalog && (
            <div className="mt-4">
              <Input
                label={`Search API symbols (PyMuPDF ${catalog.version})`}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <div className="mt-4 max-h-80 overflow-auto">
                {catalog.symbols
                  .filter((item) =>
                    `${item.name} ${item.members.join(" ")}`
                      .toLowerCase()
                      .includes(query.toLowerCase()),
                  )
                  .map((item) => (
                    <details key={item.name}>
                      <summary className="cursor-pointer py-2 font-medium">
                        {item.name}
                      </summary>
                      <p className="break-words text-sm">
                        {item.members.join(", ") ||
                          "Module-level callable; reference only."}
                      </p>
                    </details>
                  ))}
              </div>
            </div>
          )}
        </BodyCard>
      </div>
    </AppShell>
  );
}
