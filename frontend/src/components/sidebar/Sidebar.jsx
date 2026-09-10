import { useId, useState } from "react";
import { cx } from "@components/utils";

export function SidebarButton({ active, children, className, ...props }) {
  return (
    <button
      type="button"
      {...props}
      aria-current={active ? "page" : undefined}
      className={cx(
        "w-full rounded-lg border-0 px-4 py-3 text-left text-sm cursor-pointer focus-visible:outline-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed",
        active
          ? "bg-white text-slate-950 font-semibold shadow-sm"
          : "bg-transparent text-slate-700 hover:bg-white/60",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function SidebarGroup({ label, children, defaultExpanded = false }) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const id = useId();
  return (
    <div>
      <SidebarButton
        aria-expanded={expanded}
        aria-controls={id}
        onClick={() => setExpanded(!expanded)}
      >
        <span className="flex justify-between gap-2">
          {label}
          <span aria-hidden="true">{expanded ? "−" : "+"}</span>
        </span>
      </SidebarButton>
      <div
        id={id}
        hidden={!expanded}
        className="ml-4 border-l border-solid border-slate-300 pl-2"
      >
        {children}
      </div>
    </div>
  );
}

function Items({ items, selectedId, onSelect }) {
  return items.map((item) =>
    item.children?.length ? (
      <SidebarGroup
        key={item.id}
        label={item.label}
        defaultExpanded={contains(item, selectedId)}
      >
        <Items
          items={item.children}
          selectedId={selectedId}
          onSelect={onSelect}
        />
      </SidebarGroup>
    ) : (
      <SidebarButton
        key={item.id}
        active={selectedId === item.id}
        disabled={item.disabled}
        onClick={() => onSelect?.(item.id)}
      >
        {item.label}
      </SidebarButton>
    ),
  );
}
function contains(item, id) {
  return item.id === id || item.children?.some((child) => contains(child, id));
}

export function Sidebar({ title, items = [], selectedId, onSelect, children }) {
  return (
    <aside className="box-border w-full shrink-0 bg-white/40 p-4 md:w-60">
      <nav aria-label={title || "Tools"}>
        <h2 className="m-0 mb-3 px-4 text-xs font-semibold uppercase tracking-wider text-slate-600">
          {title}
        </h2>
        <div className="flex flex-col gap-1">
          <Items items={items} selectedId={selectedId} onSelect={onSelect} />
          {children}
        </div>
      </nav>
    </aside>
  );
}
