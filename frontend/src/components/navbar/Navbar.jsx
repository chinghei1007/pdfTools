import { Button } from "@components/buttons/Button";
import { Dropdown } from "@components/dropdown/Dropdown";

export function Navbar({
  brand = "PDF Toolkit",
  categories = [],
  categoryId,
  onCategoryChange,
  onHistory,
  onAccount,
  accountLabel = "Log in",
  engineSwitch,
  themeControl,
  busy = false,
}) {
  return (
    <header className="pdf-navbar">
      <span className="pdf-navbar__brand">{brand}</span>
      {engineSwitch}
      {onHistory && (
        <Button variant="secondary" onClick={onHistory}>
          History
        </Button>
      )}
      {themeControl}
      {onAccount && <Button variant="ghost" onClick={onAccount}>{accountLabel}</Button>}
      {categories.length > 0 && (
        <Dropdown
          label="Menu"
          items={categories}
          value={categoryId}
          onSelect={onCategoryChange}
          disabled={busy}
        />
      )}
    </header>
  );
}
