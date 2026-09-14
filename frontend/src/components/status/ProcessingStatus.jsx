export function FileProgress({ value, label = "Processing" }) {
  const progress = Number.isFinite(value)
    ? Math.min(100, Math.max(0, value))
    : undefined;
  return (
    <div className="pdf-progress" role="status">
      <span className="pdf-progress__label">
        {label}
        {progress !== undefined && ` · ${Math.round(progress)}%`}
      </span>
      <progress
        aria-label={label}
        value={progress}
        max={100}
        className="pdf-progress__bar"
      />
    </div>
  );
}

export function ProcessingStatus({ status = "idle", progress, message }) {
  if (status === "idle" || status === "ready") return null;
  if (status === "reading" || status === "queued" || status === "running")
    return (
      <FileProgress
        value={progress}
        label={
          message ||
          {
            reading: "Reading files",
            queued: "Waiting to process",
            running: "Processing files",
          }[status]
        }
      />
    );
  return (
    <p
      role={status === "failed" ? "alert" : "status"}
      className={status === "failed" ? "pdf-error" : "pdf-success"}
    >
      {message ||
        (status === "failed"
          ? "Processing failed. Please try again."
          : "Processing complete.")}
    </p>
  );
}
