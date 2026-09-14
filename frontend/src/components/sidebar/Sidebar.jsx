import { useId, useState } from "react";
import { cx } from "@components/utils";

export function SidebarButton({ active, children, className, ...props }) {
  return (
    <button
      type="button"
      {...props}
      aria-current={active ? "page" : undefined}
      className={cx(
        "pdf-sidebar__button",
        active && "pdf-sidebar__button--active",
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
    <div className="pdf-sidebar__group">
      <SidebarButton
        aria-expanded={expanded}
        aria-controls={id}
        onClick={() => setExpanded(!expanded)}
      >
        <span className="pdf-sidebar__group-label">
          {label}
          <span aria-hidden="true">{expanded ? "−" : "+"}</span>
        </span>
      </SidebarButton>
      <div
        id={id}
        hidden={!expanded}
        className="pdf-sidebar__children"
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
    <aside className="pdf-sidebar">
      <nav aria-label={title || "Tools"}>
        <h2 className="pdf-sidebar__title">
          {title}
        </h2>
        <div className="pdf-sidebar__items">
          <Items items={items} selectedId={selectedId} onSelect={onSelect} />
          {children}
        </div>
      </nav>
    </aside>
  );
}
