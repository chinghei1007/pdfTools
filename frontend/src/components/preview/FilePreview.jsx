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
  const source = url || (local?.file === file ? local.url : undefined);
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
        className="block h-40 w-full rounded-lg bg-slate-100 object-contain"
      />
    );
  if (source && mediaType === "application/pdf" && renderPdf)
    return (
      <object
        data={source}
        type="application/pdf"
        aria-label={`Preview of ${name}`}
        className="h-96 w-full"
      >
        <p className="text-sm text-slate-600">
          Inline PDF preview is unavailable. Use the download action to open the
          file.
        </p>
      </object>
    );
  return (
    <div className="flex h-32 items-center justify-center rounded-lg bg-slate-100 text-sm font-semibold text-slate-600">
      {mediaType === "application/pdf" ? "PDF document" : "Preview unavailable"}
    </div>
  );
}
