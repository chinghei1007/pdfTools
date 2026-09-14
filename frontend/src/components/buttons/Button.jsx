import { cx } from "@components/utils";

const variants = { primary: "pdf-button--primary", secondary: "pdf-button--secondary", ghost: "pdf-button--ghost", danger: "pdf-button--danger" };
const sizes = { sm: "pdf-button--small", md: "pdf-button--medium", lg: "pdf-button--large" };

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  type = "button",
  className,
  children,
  ...props
}) {
  return (
    <button
      {...props}
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cx(
        "pdf-button",
        variants[variant],
        sizes[size],
        className,
      )}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="pdf-button__spinner"
        />
      )}
      {children}
    </button>
  );
}

export function IconButton({ label, children, ...props }) {
  return (
    <Button variant="ghost" {...props} aria-label={label} title={label}>
      {children}
    </Button>
  );
}

export function CloseButton({ label = "Close", ...props }) {
  return (
    <IconButton {...props} label={label}>
      <span aria-hidden="true">×</span>
    </IconButton>
  );
}
