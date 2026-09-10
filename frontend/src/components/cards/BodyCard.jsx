import { cx } from "@components/utils";

export function BodyCard({ title, description, children, footer, className }) {
  return (
    <section
      className={cx(
        "box-border rounded-2xl border border-solid border-slate-200 bg-white p-5 shadow-sm md:p-7",
        className,
      )}
    >
      {(title || description) && (
        <header className="mb-5">
          {title && (
            <h2 className="m-0 text-xl font-semibold text-slate-900">
              {title}
            </h2>
          )}
          {description && (
            <p className="mt-2 text-sm text-slate-600">{description}</p>
          )}
        </header>
      )}
      {children}
      {footer && (
        <footer className="mt-5 flex flex-wrap items-center justify-end gap-3">
          {footer}
        </footer>
      )}
    </section>
  );
}
