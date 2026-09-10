export function FileProgress({ value, label = "Processing" }) {
  const progress = Number.isFinite(value)
    ? Math.min(100, Math.max(0, value))
    : undefined;
  return (
    <div className="flex flex-col gap-2" role="status">
      <span className="text-sm text-slate-700">
        {label}
        {progress !== undefined && ` · ${Math.round(progress)}%`}
      </span>
      <progress
        aria-label={label}
        value={progress}
        max={100}
        className="h-2 w-full accent-slate-900"
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
      className={
        status === "failed"
          ? "m-0 text-sm text-red-700"
          : "m-0 text-sm text-green-700"
      }
    >
      {message ||
        (status === "failed"
          ? "Processing failed. Please try again."
          : "Processing complete.")}
    </p>
  );
}
