import { useEffect, useState } from "react";

export function FilePreview({
  file,
  url,
  name = file?.name || "Document",
  mediaType = file?.type || "",
  renderPdf = false,
}) {
  const [local, setLocal] = useState(null);
  useEffect(() => {
    if (!file || url) return;
    const objectUrl = URL.createObjectURL(file);
    // Synchronize a browser-owned resource; cleanup must also work in StrictMode.
    // oxlint-disable-next-line react/set-state-in-effect
    setLocal({ file, url: objectUrl });
    return () => URL.revokeObjectURL(objectUrl);
  }, [file, url]);
  // Server records have neither a local File nor a URL while rendering is pending.
  // Optional chaining alone makes undefined === undefined true in that state.
  const source = url || (local && local.file === file ? local.url : undefined);
  if (
    source &&
    [
      "image/jpeg",
      "image/png",
      "image/webp",
      "image/gif",
      "image/avif",
    ].includes(mediaType)
  )
    return (
      <img
        src={source}
        alt={`Preview of ${name}`}
        className="pdf-file-preview__image"
      />
    );
  if (source && mediaType === "application/pdf" && renderPdf)
    return (
      <object
        data={source}
        type="application/pdf"
        aria-label={`Preview of ${name}`}
        className="pdf-file-preview__document"
      >
        <p className="pdf-muted">
          Inline PDF preview is unavailable. Use the download action to open the
          file.
        </p>
      </object>
    );
  return (
    <div className="pdf-file-preview__fallback">
      {mediaType === "application/pdf" ? "PDF document" : "Preview unavailable"}
    </div>
  );
}
