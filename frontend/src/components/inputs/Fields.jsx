import { useId } from "react";
import { cx } from "@components/utils";

const control =
  "pdf-field__control";

function Field({ label, hint, error, id, children }) {
  return (
    <div className="pdf-field">
      <label htmlFor={id} className="pdf-field__label">
        {label}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="pdf-field__hint">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="pdf-field__error">
          {error}
        </p>
      )}
    </div>
  );
}

function useField(id, hint, error) {
  const generated = useId();
  const fieldId = id ?? generated;
  return {
    id: fieldId,
    "aria-invalid": error ? true : undefined,
    "aria-describedby":
      [hint && `${fieldId}-hint`, error && `${fieldId}-error`]
        .filter(Boolean)
        .join(" ") || undefined,
  };
}

export function Input({ label, hint, error, id, className, ...props }) {
  const a11y = useField(id, hint, error);
  return (
    <Field {...{ label, hint, error }} id={a11y.id}>
      <input {...props} {...a11y} className={cx(control, className)} />
    </Field>
  );
}

export function Select({
  label,
  hint,
  error,
  id,
  options,
  className,
  ...props
}) {
  const a11y = useField(id, hint, error);
  return (
    <Field {...{ label, hint, error }} id={a11y.id}>
      <select {...props} {...a11y} className={cx(control, className)}>
        {options.map(({ value, label: text, disabled }) => (
          <option key={value} value={value} disabled={disabled}>
            {text}
          </option>
        ))}
      </select>
    </Field>
  );
}

export function Slider({
  label,
  hint,
  error,
  id,
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  ...props
}) {
  const a11y = useField(id, hint, error);
  return (
    <Field label={`${label}: ${value}`} hint={hint} error={error} id={a11y.id}>
      <input
        {...props}
        {...a11y}
        className="pdf-field__range"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange?.(Number(event.target.value))}
      />
    </Field>
  );
}
