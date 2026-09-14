import { cx } from "@components/utils";

export function BodyCard({ title, description, children, footer, className }) {
  return (
    <section
      className={cx("pdf-card", className)}
    >
      {(title || description) && (
        <header className="pdf-card__header">
          {title && (
            <h2 className="pdf-card__title">
              {title}
            </h2>
          )}
          {description && (
            <p className="pdf-card__description">{description}</p>
          )}
        </header>
      )}
      {children}
      {footer && (
        <footer className="pdf-card__footer">
          {footer}
        </footer>
      )}
    </section>
  );
}
