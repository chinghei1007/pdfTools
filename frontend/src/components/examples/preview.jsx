import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import { toolRegistry } from '@components/examples/toolRegistry';
import { logUploadEvent } from '@components/upload/events';
import {
  AppShell,
  Navbar,
  Sidebar,
  ToolWorkspace,
  FileDropzone,
  FileCollection,
  Input,
  Select,
  Slider,
  Button,
  BodyCard,
  HistoryDialog,
  LoginDialog,
  ResultPanel,
} from "@components";

// This file is an isolated HTML entry, not a reusable refresh boundary.
// oxlint-disable-next-line react/only-export-components
function ComponentPreview() {
  const [dialog, setDialog] = useState(null);
  const [files, setFiles] = useState([]);
  const [view, setView] = useState("grid");
  const [quality, setQuality] = useState(80);
  const [format, setFormat] = useState("pdf");
  const [name, setName] = useState("document");
  const [category, setCategory] = useState("conversion");
  const [tool, setTool] = useState("image-to-pdf");
  const config = toolRegistry[tool];
  const chooseTool = (id) => {
    setTool(id);
    setFiles([]);
    setFormat(toolRegistry[id].formats[0]);
    setQuality(80);
    logUploadEvent('tool.changed', { tool: id, selectionCleared: true });
  };
  const categories = [
    { id: "conversion", label: "Conversion" },
    { id: "extract", label: "Extract" },
    { id: "tools", label: "Tools" },
  ];
  const groups = {
    conversion: [
      { id: "image-to-pdf", label: "Image to PDF" },
      { id: "pdf-to-image", label: "PDF to Image" },
    ],
    extract: [
      { id: "images", label: "Images" },
      { id: "metadata", label: "Metadata" },
    ],
    tools: [
      {
        id: "pages",
        label: "Pages",
        children: [
          { id: "merge", label: "Merge" },
          { id: "split", label: "Split" },
          { id: "rotate", label: "Rotate" },
        ],
      },
    ],
  };
  return (
    <AppShell
      navbar={
        <Navbar
          categories={categories}
          categoryId={category}
          onCategoryChange={(id) => { setCategory(id); chooseTool({ conversion: 'image-to-pdf', extract: 'images', tools: 'merge' }[id]); }}
          onHistory={() => setDialog("history")}
          onAccount={() => setDialog("login")}
        />
      }
      sidebar={
        <Sidebar
          key={category}
          title={category}
          items={groups[category]}
          selectedId={tool}
          onSelect={chooseTool}
        />
      }
      overlays={
        <>
          <HistoryDialog
            open={dialog === "history"}
            onClose={() => setDialog(null)}
            entries={[]}
          />
          <LoginDialog
            open={dialog === "login"}
            onClose={() => setDialog(null)}
          />
        </>
      }
    >
      <ToolWorkspace
        title="Component preview"
        description="UI examples only. Processing and authentication are not connected."
        upload={
          <FileDropzone
            key={tool}
            type={config.type}
            multiple={config.multiple}
            maxSizeBytes={20 * 1024 * 1024}
            onFilesSelected={(selected) => {
              logUploadEvent('selection.stored_locally', { count: selected.length });
              logUploadEvent('upload.skipped', { reason: 'No upload API configured; no database save occurred.' });
              if (config.type === 'pdf') logUploadEvent('preview.request.skipped', { page: 1, reason: 'No server file ID or preview API configured.' });
              setFiles((previous) => [
                ...(config.multiple ? previous : []),
                ...selected.map((file) => ({ id: crypto.randomUUID(), file })),
              ]);
            }}
          />
        }
        preview={
          <FileCollection
            files={files}
            view={view}
            onViewChange={setView}
            onRemove={(id) =>
              setFiles((previous) =>
                previous.filter((entry) => entry.id !== id),
              )
            }
            onReorder={(from, to) =>
              setFiles((previous) => {
                const next = [...previous];
                const [entry] = next.splice(from, 1);
                next.splice(to, 0, entry);
                return next;
              })
            }
          />
        }
        settings={
          <>
            <Input
              label="Output name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <Select
              label="Output format"
              value={format}
              onChange={(event) => setFormat(event.target.value)}
              options={config.formats.map((value) => ({ value, label: value.toUpperCase() }))}
            />
            {format === 'jpg' && <Slider label="Quality" value={quality} onChange={setQuality} />}
          </>
        }
        result={<ResultPanel />}
      />
      <div className="mx-auto mt-6 max-w-5xl">
        <BodyCard title="Button variants">
          <div className="flex flex-wrap gap-3">
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="danger">Danger</Button>
            <Button disabled>Disabled</Button>
            <Button loading>Processing</Button>
          </div>
        </BodyCard>
      </div>
    </AppShell>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ComponentPreview />
  </StrictMode>,
);
