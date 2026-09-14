import { useEffect, useId, useRef, useState } from "react";
import { Button } from "@components/buttons/Button";

// Disclosure with ordinary buttons: Tab navigates the choices, Escape closes.
export function Dropdown({
  label = "Menu",
  items,
  value,
  onSelect,
  disabled = false,
}) {
  const [open, setOpen] = useState(false);
  const root = useRef(null);
  const trigger = useRef(null);
  const id = useId();
  useEffect(() => {
    if (!open) return;
    const dismiss = (event) => {
      if (!root.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open]);
  return (
    <div
      ref={root}
      className="pdf-dropdown"
      onBlur={(event) => {
        // Opening browser DevTools reports no next DOM focus target. Keep the
        // disclosure mounted so its styles can be inspected; real keyboard
        // focus moves still provide relatedTarget and dismiss normally.
        if (
          event.relatedTarget &&
          !event.currentTarget.contains(event.relatedTarget)
        )
          setOpen(false);
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          trigger.current?.focus();
        }
      }}
    >
      <Button
        ref={trigger}
        disabled={disabled}
        aria-expanded={open && !disabled}
        aria-controls={id}
        onClick={() => setOpen(!open)}
      >
        {label}
        <span aria-hidden="true">▾</span>
      </Button>
      {open && !disabled && (
        <div
          id={id}
          className="pdf-dropdown__menu"
        >
          {items.map((item) => (
            <Button
              key={item.id}
              variant={value === item.id ? "secondary" : "ghost"}
              className="pdf-dropdown__item"
              disabled={item.disabled}
              aria-pressed={value === item.id}
              onClick={() => {
                setOpen(false);
                trigger.current?.focus();
                onSelect?.(item.id);
              }}
            >
              {item.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
