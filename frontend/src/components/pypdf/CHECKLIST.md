# pypdf unified workbench verification

The machine-readable 56-function audit is maintained in `backend/component/pymupdfService/pypdf_checklist.json`. The unified catalog now reports 55 functions as available and `flatten_pdf` as PyMuPDF-assisted.

All page inputs exposed by the UI are 1-based. The Python helper modules continue to use their native 0-based indices internally.

## Coverage added by the unified workbench

- Safe visitor-position text extraction (`visitor-text`) without accepting executable callbacks.
- Image presence checks (`image-check`).
- Free text, rectangle, ellipse, line, polygon, highlight, text-note, internal-link, and URI-link annotations (`add-annotation`).
- Text-only form fields and named field inspection.
- Factor or target-size page scaling.
- Overlay, underlay, and insert-page operations.
- Attachment add/remove operations.
- Flat and nested bookmark creation.
- Reconstructed content-stream line segments.
- User/owner password and permission controls.

`Underline`, `Squiggly`, and `StrikeOut` are deliberately unsupported. `PolyLine` and `Popup` are not exposed as workbench functions.

Run the backend unittest modules to verify the catalog, every operation adapter, supported annotations, shared History, secret redaction, and browser isolation.
