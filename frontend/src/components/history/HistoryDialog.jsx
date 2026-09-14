import { Dialog } from "@components/dialogs/Dialog";
import { Button } from "@components/buttons/Button";
import { Select } from "@components/inputs/Fields";
import { ENGINES, engineColor } from "@/theme";

export function HistoryDialog({
  open, onClose, entries = [], loading = false, error, onSelect,
  engine = "", toolId = "", tools = [], onEngineChange, onToolChange,
  onLoadMore, hasMore = false, selectionDisabled = false,
}) {
  return (
    <Dialog open={open} onClose={onClose} title="History" description="Previous jobs saved for this browser.">
      <div className="pdf-history">
        <div className="pdf-history__filters">
          <Select label="Engine" value={engine} onChange={(event) => onEngineChange?.(event.target.value)} options={[
            { value: "", label: "All engines" },
            ...ENGINES.map(({ id, label }) => ({ value: id, label })),
          ]} />
          <Select label="Tool" value={toolId} onChange={(event) => onToolChange?.(event.target.value)} options={[
            { value: "", label: "All tools" },
            ...tools.map((tool) => ({ value: tool.id, label: tool.label })),
          ]} />
        </div>
        {loading && !entries.length ? (
          <progress className="pdf-progress__bar" aria-label="Loading history" />
        ) : error ? (
          <p role="alert" className="pdf-error">{error}</p>
        ) : !entries.length ? (
          <p className="pdf-muted">No history matches these filters.</p>
        ) : (
          <ul className="pdf-history__list">
            {entries.map((entry) => {
              const config = ENGINES.find((item) => item.id === entry.engine);
              const inputNames = entry.inputs?.map((file) => file?.name).filter(Boolean).join(", ");
              const available = entry.outputs?.some((file) => file?.available);
              return (
                <li key={entry.id} className="pdf-history__entry">
                  <button type="button" className="pdf-history__entry-button" disabled={selectionDisabled} onClick={() => onSelect?.(entry)}>
                    <span className="pdf-history__engine" style={{ "--pdf-history-engine": config ? engineColor(config) : "currentColor" }}>
                      {config?.label || entry.engine}
                    </span>
                    <span className="pdf-history__summary">
                      <strong>{entry.toolLabel || entry.toolId}</strong>
                      <small>{inputNames || "No uploaded input"}</small>
                    </span>
                    <span className={`pdf-history__status pdf-history__status--${entry.status}`}>
                      {entry.status}{entry.status === "completed" && !available ? " · output unavailable" : ""}
                    </span>
                    <time dateTime={entry.createdAt}>{new Date(entry.createdAt).toLocaleString()}</time>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
        {hasMore && <div className="pdf-history__more"><Button variant="secondary" loading={loading} onClick={onLoadMore}>Load more</Button></div>}
      </div>
    </Dialog>
  );
}
