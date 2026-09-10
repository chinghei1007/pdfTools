import { BodyCard } from "@components/cards/BodyCard";
import { FileItem } from "@components/preview/FileCollection";
import { Button } from "@components/buttons/Button";

export function ResultPanel({ files = [], onDownload, onReset, children }) {
  return (
    <BodyCard
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
      <div className="grid gap-3 sm:grid-cols-2">
        {files.map((entry) => (
          <FileItem
            key={entry.id}
            entry={entry}
            actions={
              <Button
                disabled={!onDownload}
                onClick={() => onDownload?.(entry)}
              >
                Download
              </Button>
            }
          />
        ))}
      </div>
      {!files.length && (
        <p className="text-sm text-slate-600">No output files available.</p>
      )}
      {children}
    </BodyCard>
  );
}
