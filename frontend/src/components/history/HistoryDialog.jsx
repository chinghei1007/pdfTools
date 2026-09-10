import { Dialog } from "@components/dialogs/Dialog";
import { Button } from "@components/buttons/Button";

export function HistoryDialog({
  open,
  onClose,
  entries = [],
  loading = false,
  error,
  onSelect,
}) {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="History"
      description="Your previous document jobs."
    >
      {loading ? (
        <p role="status">Loading history…</p>
      ) : error ? (
        <p role="alert" className="text-red-700">
          {error}
        </p>
      ) : !entries.length ? (
        <p className="text-sm text-slate-600">No history yet.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="rounded-lg border border-solid border-slate-200 p-3"
            >
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium">{entry.label}</span>
                {onSelect && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => onSelect(entry)}
                  >
                    View
                  </Button>
                )}
              </div>
              <p className="mt-2 text-xs text-slate-600">
                {entry.status}
                {entry.createdAt && (
                  <>
                    {" "}
                    ·{" "}
                    <time dateTime={entry.createdAt}>
                      {new Date(entry.createdAt).toLocaleString()}
                    </time>
                  </>
                )}
              </p>
            </li>
          ))}
        </ul>
      )}
    </Dialog>
  );
}
