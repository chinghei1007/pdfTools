import "@components/styles.css";

export function AppShell({ navbar, sidebar, children, overlays }) {
  return (
    <div className="pdf-app">
      {navbar}
      <div className="pdf-layout">
        {sidebar}
        <main className="pdf-main">{children}</main>
      </div>
      {overlays}
    </div>
  );
}
