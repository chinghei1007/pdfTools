export function ThemeControl({ value, onChange }) {
  return (
    <label className="pdf-theme-control">
      <span className="pdf-visually-hidden">Theme</span>
      <select value={value} onChange={(event) => onChange?.(event.target.value)} aria-label="Theme">
        <option value="auto">Auto</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
