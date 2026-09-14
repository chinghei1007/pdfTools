import { useId, useRef, useState } from "react";
import { Button } from "@components/buttons/Button";
import { cx, formatBytes } from "@components/utils";
import { validate, inputTypes } from "@components/upload/validation";
import { logUploadEvent } from "@components/upload/events";

export function FileDropzone({
  accept = ".pdf",
  type,
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
  const select = (files, source) => {
    if (disabled) return;
    logUploadEvent('selection.received', { count: files.length, source, files: Array.from(files, (file) => ({ sizeBytes: file.size, mediaType: file.type || 'unknown' })) });
    if (!files.length && source === 'drop') {
      const message = 'No file bytes were provided by this drag. Save the document locally and use Browse files.';
      setErrors([message]);
      onValidationError?.([message]);
      logUploadEvent('validation.rejected', { source, code: 'no_files' });
      return;
    }
    const result = validate(Array.from(files), {
      type,
      accept,
      multiple,
      maxSizeBytes,
    });
    setErrors(result.errors);
    if (result.errors.length) logUploadEvent('validation.rejected', { count: result.errors.length, source, issues: result.issues });
    if (result.accepted.length) logUploadEvent('validation.accepted', { count: result.accepted.length, type: type || 'custom' });
    onValidationError?.(result.errors);
    if (result.accepted.length) onFilesSelected?.(result.accepted);
  };
  return (
    <div className="pdf-upload">
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
          select(event.dataTransfer.files, 'drop');
        }}
        className={cx(
          "pdf-upload__dropzone",
          dragging && !disabled && "pdf-upload__dropzone--dragging",
          disabled && "pdf-upload__dropzone--disabled",
        )}
      >
        <p className="pdf-upload__label">{label}</p>
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
          className="pdf-visually-hidden"
          accept={inputTypes[type] || accept}
          multiple={multiple}
          disabled={disabled}
          onChange={(event) => {
            select(event.target.files, 'browse');
            event.target.value = "";
          }}
        />
        <p id={hintId} className="pdf-upload__hint">
          {hint ||
            `${inputTypes[type] || accept || "All file types"}${maxSizeBytes ? ` · Up to ${formatBytes(maxSizeBytes)} per file` : ""}`}
        </p>
      </div>
      {errors.length > 0 && (
        <ul role="alert" className="pdf-upload__errors">
          {errors.map((error, index) => (
            <li key={`${index}-${error}`}>{error}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
