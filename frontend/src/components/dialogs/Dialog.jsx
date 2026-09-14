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
      className="pdf-dialog"
    >
      <div className="pdf-dialog__inner">
        <header className="pdf-dialog__header">
          <div>
            <h2 id={titleId} className="pdf-dialog__title">
              {title}
            </h2>
            {description && (
              <p id={descriptionId} className="pdf-dialog__description">
                {description}
              </p>
            )}
          </div>
          <CloseButton onClick={onClose} />
        </header>
        <div className="pdf-dialog__content">{open && children}</div>
        {footer && (
          <footer className="pdf-dialog__footer">{footer}</footer>
        )}
      </div>
    </dialog>
  );
}
