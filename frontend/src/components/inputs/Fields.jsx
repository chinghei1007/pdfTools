import { useId } from "react";
import { cx } from "@components/utils";

const control =
  "box-border w-full rounded-lg border border-solid border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus-visible:outline-2 focus-visible:outline-blue-600 disabled:bg-slate-100 disabled:cursor-not-allowed";

function Field({ label, hint, error, id, children }) {
  return (
    <div className="flex flex-col gap-1.5 text-left">
      <label htmlFor={id} className="text-sm font-medium text-slate-800">
        {label}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="m-0 text-xs text-slate-600">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="m-0 text-sm text-red-700">
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
        className="w-full accent-slate-900"
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
