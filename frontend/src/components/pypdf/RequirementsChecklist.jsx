import { useEffect, useState } from "react";
import { BodyCard, Input } from "@components";
import { request } from "@components/pymupdf/api";

export default function RequirementsChecklist() {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    request("/pypdf/checklist", undefined, controller.signal)
      .then(setRows)
      .catch((failure) => {
        if (failure.name !== "AbortError") setError(failure.message);
      });
    return () => controller.abort();
  }, []);
  return (
    <BodyCard
      title="Original requirements checklist"
      description="Each function from your pasted reference is listed below. Available means wired to this workbench, not that every option or real-world document has been validated."
    >
      {error && <p role="alert">{error}</p>}
      <Input
        label="Filter by function, group or status"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
      />
      <div className="pdf-checklist">
        {rows
          .filter((row) =>
            `${row.group} ${row.function} ${row.status}`
              .toLowerCase()
              .includes(filter.toLowerCase()),
          )
          .map((row) => (
            <article
              key={row.function}
              className="pdf-checklist__item"
            >
              <strong className="pdf-checklist__function">{row.function}</strong>
              <p>
                {row.group} · {row.status}
                {row.tool && ` · ${row.tool}`}
              </p>
              <p className="pdf-muted">{row.check}</p>
            </article>
          ))}
      </div>
    </BodyCard>
  );
}
