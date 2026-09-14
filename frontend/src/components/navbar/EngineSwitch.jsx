export function EngineSwitch({ engines, value, disabled, onChange }) {
  return (
    <div className="pdf-engine-switch" role="group" aria-label="PDF engine">
      {engines.map((engine) => (
        <button key={engine.id} type="button" className="pdf-engine-switch__option" aria-pressed={value === engine.id} disabled={disabled} onClick={() => onChange?.(engine.id)}>
          {engine.label}
        </button>
      ))}
    </div>
  );
}
