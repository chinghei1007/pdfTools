import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Workbench from "@components/pymupdf/Workbench";
createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Workbench engine="pypdf" />
  </StrictMode>,
);
