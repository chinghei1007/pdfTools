import { useEffect, useId, useRef } from "react";
import { CloseButton } from "@components/buttons/Button";

export function Dialog({
  open,
  onClose,
  title,
  description,
  children,
  footer,
}) {
  const ref = useRef(null);
  const titleId = useId();
  const descriptionId = useId();
  useEffect(() => {
    const dialog = ref.current;
    if (!open) {
      if (dialog.open) dialog.close();
      return;
    }
    const previous = document.activeElement;
    if (!dialog.open) dialog.showModal();
    return () => {
      if (dialog.open) dialog.close();
      previous?.focus?.();
    };
  }, [open]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          const bounds = event.currentTarget.getBoundingClientRect();
          if (
            event.clientX < bounds.left ||
            event.clientX > bounds.right ||
            event.clientY < bounds.top ||
            event.clientY > bounds.bottom
          )
            onClose();
        }
      }}
      className="pdf-ui w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-2xl border-0 bg-white p-0 text-slate-900 shadow-xl backdrop:bg-slate-950/50"
    >
      <div className="p-6 text-left">
        <header className="flex items-start justify-between gap-4">
          <div>
            <h2 id={titleId} className="m-0 text-xl font-semibold">
              {title}
            </h2>
            {description && (
              <p id={descriptionId} className="mt-2 text-sm text-slate-600">
                {description}
              </p>
            )}
          </div>
          <CloseButton onClick={onClose} />
        </header>
        <div className="mt-5">{open && children}</div>
        {footer && (
          <footer className="mt-5 flex justify-end gap-2">{footer}</footer>
        )}
      </div>
    </dialog>
  );
}
