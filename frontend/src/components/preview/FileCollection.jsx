import { Button, IconButton } from "@components/buttons/Button";
import { FilePreview } from "@components/preview/FilePreview";
import { FileProgress } from "@components/status/ProcessingStatus";
import { cx, formatBytes } from "@components/utils";

// Entries: { id, file?, name?, size?, mediaType?, url?, error?, progress? }.
export function FileItem({ entry, onRemove, actions }) {
  const name = entry.name || entry.file?.name || "Untitled file";
  return (
    <article className="min-w-0 rounded-xl border border-solid border-slate-200 bg-white p-3">
      <FilePreview
        file={entry.file}
        url={entry.url}
        name={name}
        mediaType={entry.mediaType || entry.file?.type}
      />
      <div className="mt-3 flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <p className="m-0 break-all text-sm font-medium">{name}</p>
          <p className="mt-1 text-xs text-slate-600">
            {formatBytes(entry.size ?? entry.file?.size ?? 0)}
          </p>
        </div>
        {onRemove && (
          <IconButton
            label={`Remove ${name}`}
            onClick={() => onRemove(entry.id)}
          >
            ×
          </IconButton>
        )}
      </div>
      {entry.progress !== undefined && (
        <FileProgress value={entry.progress} label="Reading file" />
      )}
      {entry.error && (
        <p role="alert" className="text-sm text-red-700">
          {entry.error}
        </p>
      )}
      {actions && <div className="mt-3 flex flex-wrap gap-2">{actions}</div>}
    </article>
  );
}

export function FileCollection({
  files = [],
  view = "grid",
  onViewChange,
  onRemove,
  onReorder,
}) {
  return (
    <div>
      {onViewChange && (
        <div
          className="mb-3 flex justify-end gap-2"
          role="group"
          aria-label="Preview layout"
        >
          {["grid", "list"].map((mode) => (
            <Button
              key={mode}
              variant="secondary"
              size="sm"
              aria-pressed={view === mode}
              onClick={() => onViewChange(mode)}
            >
              {mode === "grid" ? "Grid" : "List"}
            </Button>
          ))}
        </div>
      )}
      {!files.length ? (
        <p className="text-sm text-slate-600">No files selected.</p>
      ) : (
        <div
          className={cx(
            "grid gap-3",
            view === "grid" && "sm:grid-cols-2 lg:grid-cols-3",
          )}
        >
          {files.map((entry, index) => (
            <FileItem
              key={entry.id}
              entry={entry}
              onRemove={onRemove}
              actions={
                onReorder && (
                  <>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={index === 0}
                      aria-label={`Move ${entry.name || entry.file?.name} earlier`}
                      onClick={() => onReorder(index, index - 1)}
                    >
                      Move earlier
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={index === files.length - 1}
                      aria-label={`Move ${entry.name || entry.file?.name} later`}
                      onClick={() => onReorder(index, index + 1)}
                    >
                      Move later
                    </Button>
                  </>
                )
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
