import { BodyCard } from "@components/cards/BodyCard";
import { Button } from "@components/buttons/Button";
import { ProcessingStatus } from "@components/status/ProcessingStatus";

export function ToolHeader({ title, description }) {
  return (
    <header className="pdf-workspace__header">
      <h1 className="pdf-workspace__title">{title}</h1>
      {description && (
        <p className="pdf-workspace__description">{description}</p>
      )}
    </header>
  );
}

export function ToolOptions({ children, disabled = false }) {
  return (
    <fieldset
      disabled={disabled}
      className="pdf-settings pdf-settings--stacked"
    >
      <legend>Settings</legend>
      {children}
    </fieldset>
  );
}

export function ToolWorkspace({
  title,
  description,
  upload,
  preview,
  settings,
  result,
  status = "idle",
  progress,
  message,
  onRun,
  canRun = false,
  actionLabel = "Process files",
}) {
  const busy = ["reading", "queued", "running"].includes(status);
  return (
    <div className="pdf-workspace">
      <ToolHeader title={title} description={description} />
      {upload && <BodyCard title="Upload files">{upload}</BodyCard>}
      {preview && <BodyCard title="Upload preview">{preview}</BodyCard>}
      {settings && (
        <BodyCard>
          <ToolOptions disabled={busy}>{settings}</ToolOptions>
        </BodyCard>
      )}
      <div className="pdf-workspace__status">
        <ProcessingStatus
          status={status}
          progress={progress}
          message={message}
        />
        <div className="pdf-workspace__actions">
          <Button disabled={!canRun || !onRun} loading={busy} onClick={onRun}>
            {actionLabel}
          </Button>
        </div>
      </div>
      {result}
    </div>
  );
}
