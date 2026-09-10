import { cx } from "@components/utils";

const variants = {
  primary: "bg-slate-900 text-white border-slate-900 hover:bg-slate-700",
  secondary: "bg-white text-slate-900 border-slate-300 hover:bg-slate-50",
  ghost: "bg-transparent text-slate-700 border-transparent hover:bg-slate-100",
  danger: "bg-red-700 text-white border-red-700 hover:bg-red-800",
};
const sizes = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-3 text-base",
};

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
        "inline-flex items-center justify-center gap-2 rounded-lg border border-solid font-medium cursor-pointer transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className,
      )}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="size-4 rounded-full border-2 border-solid border-current border-t-transparent motion-safe:animate-spin"
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
