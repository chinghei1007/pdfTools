import "@components/styles.css";

export function AppShell({ navbar, sidebar, children, overlays }) {
  return (
    <div className="pdf-ui min-h-screen bg-slate-50 font-sans text-slate-900 text-left">
      {navbar}
      <div className="flex flex-col md:flex-row">
        {sidebar}
        <main className="min-w-0 flex-1 p-4 md:p-8">{children}</main>
      </div>
      {overlays}
    </div>
  );
}
