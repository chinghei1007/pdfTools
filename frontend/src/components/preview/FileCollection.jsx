import { Button, IconButton } from "@components/buttons/Button";
import { FilePreview } from "@components/preview/FilePreview";
import { FileProgress } from "@components/status/ProcessingStatus";
import { cx, formatBytes } from "@components/utils";

// Entries: { id, file?, name?, size?, mediaType?, url?, error?, progress? }.
export function FileItem({ entry, onRemove, actions }) {
  const name = entry.name || entry.file?.name || "Untitled file";
  return (
    <article className="pdf-file-item">
      <FilePreview
        file={entry.file}
        url={entry.url}
        name={name}
        mediaType={entry.mediaType || entry.file?.type}
      />
      <div className="pdf-file-item__details">
        <div className="pdf-file-item__text">
          <p className="pdf-file-item__name">{name}</p>
          <p className="pdf-file-item__size">
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
        <p role="alert" className="pdf-error">
          {entry.error}
        </p>
      )}
      {actions && <div className="pdf-file-item__actions">{actions}</div>}
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
    <div className="pdf-file-collection">
      {onViewChange && (
        <div
          className="pdf-file-collection__view"
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
        <p className="pdf-muted">No files selected.</p>
      ) : (
        <div
          className={cx(
            "pdf-file-collection__items",
            view === "grid" && "pdf-file-collection__items--grid",
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
