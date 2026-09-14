import { BodyCard } from "@components/cards/BodyCard";
import { FileItem } from "@components/preview/FileCollection";
import { Button } from "@components/buttons/Button";

export function ResultPanel({ files = [], onDownload, onReset, children }) {
  return (
    <BodyCard
      className="pdf-result"
      title="Final preview"
      description="Review your processed files."
      footer={
        onReset && (
          <Button variant="secondary" onClick={onReset}>
            Start again
          </Button>
        )
      }
    >
      <div className="pdf-result__files">
        {files.map((entry) => (
          <FileItem
            key={entry.id}
            entry={entry}
            actions={
              <Button
                disabled={!onDownload || entry.available === false}
                onClick={() => onDownload?.(entry)}
              >
                {entry.available === false ? "Unavailable" : "Download"}
              </Button>
            }
          />
        ))}
      </div>
      {!files.length && (
        <p className="pdf-muted">No output files available.</p>
      )}
      {children}
    </BodyCard>
  );
}
