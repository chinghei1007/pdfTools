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
}) {
  return (
    <header className="sticky top-0 z-10 flex flex-wrap items-center gap-3 border-b border-solid border-slate-200 bg-white px-5 py-4">
      <span className="mr-auto text-lg font-bold">{brand}</span>
      <Button variant="secondary" onClick={onHistory} disabled={!onHistory}>
        History
      </Button>
      <Button variant="ghost" onClick={onAccount} disabled={!onAccount}>
        {accountLabel}
      </Button>
      {categories.length > 0 && (
        <Dropdown
          label="Menu"
          items={categories}
          value={categoryId}
          onSelect={onCategoryChange}
        />
      )}
    </header>
  );
}
