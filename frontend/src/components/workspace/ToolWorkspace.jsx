import { BodyCard } from "@components/cards/BodyCard";
import { Button } from "@components/buttons/Button";
import { ProcessingStatus } from "@components/status/ProcessingStatus";

export function ToolHeader({ title, description }) {
  return (
    <header>
      <h1 className="m-0 text-2xl font-bold text-slate-900">{title}</h1>
      {description && (
        <p className="mt-2 text-sm text-slate-600">{description}</p>
      )}
    </header>
  );
}

export function ToolOptions({ children, disabled = false }) {
  return (
    <fieldset
      disabled={disabled}
      className="m-0 flex min-w-0 flex-col gap-4 border-0 p-0"
    >
      <legend className="mb-4 text-base font-semibold">Settings</legend>
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
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <ToolHeader title={title} description={description} />
      {upload && <BodyCard title="Upload files">{upload}</BodyCard>}
      {preview && <BodyCard title="Upload preview">{preview}</BodyCard>}
      {settings && (
        <BodyCard>
          <ToolOptions disabled={busy}>{settings}</ToolOptions>
        </BodyCard>
      )}
      <div className="flex flex-col gap-4">
        <ProcessingStatus
          status={status}
          progress={progress}
          message={message}
        />
        <div>
          <Button disabled={!canRun || !onRun} loading={busy} onClick={onRun}>
            {actionLabel}
          </Button>
        </div>
      </div>
      {result}
    </div>
  );
}
