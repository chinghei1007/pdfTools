import { useId, useRef, useState } from "react";
import { Button } from "@components/buttons/Button";
import { cx, formatBytes } from "@components/utils";
import { validateFiles } from "@components/upload/validation";

export function FileDropzone({
  accept = ".pdf",
  multiple = true,
  maxSizeBytes,
  disabled = false,
  onFilesSelected,
  onValidationError,
  label = "Drop files here",
  hint,
}) {
  const input = useRef(null);
  const depth = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [errors, setErrors] = useState([]);
  const hintId = useId();
  const select = (files) => {
    if (disabled) return;
    const result = validateFiles(Array.from(files), {
      accept,
      multiple,
      maxSizeBytes,
    });
    setErrors(result.errors);
    onValidationError?.(result.errors);
    if (result.accepted.length) onFilesSelected?.(result.accepted);
  };
  return (
    <div>
      <div
        onDragOver={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = disabled ? "none" : "copy";
        }}
        onDragEnter={(event) => {
          event.preventDefault();
          if (!disabled) {
            depth.current++;
            setDragging(true);
          }
        }}
        onDragLeave={() => {
          depth.current = Math.max(0, depth.current - 1);
          if (!depth.current) setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          depth.current = 0;
          setDragging(false);
          select(event.dataTransfer.files);
        }}
        className={cx(
          "rounded-xl border-2 border-dashed p-8 text-center",
          dragging && !disabled
            ? "border-blue-600 bg-blue-50"
            : "border-slate-300 bg-slate-50",
          disabled && "opacity-50",
        )}
      >
        <p className="m-0 mb-3 font-medium text-slate-800">{label}</p>
        <Button
          variant="secondary"
          disabled={disabled}
          aria-describedby={hintId}
          onClick={() => input.current?.click()}
        >
          Browse files
        </Button>
        <input
          ref={input}
          type="file"
          className="hidden"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={(event) => {
            select(event.target.files);
            event.target.value = "";
          }}
        />
        <p id={hintId} className="mt-3 text-xs text-slate-600">
          {hint ||
            `${accept || "All file types"}${maxSizeBytes ? ` · Up to ${formatBytes(maxSizeBytes)} per file` : ""}`}
        </p>
      </div>
      {errors.length > 0 && (
        <ul role="alert" className="text-sm text-red-700">
          {errors.map((error, index) => (
            <li key={`${index}-${error}`}>{error}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
