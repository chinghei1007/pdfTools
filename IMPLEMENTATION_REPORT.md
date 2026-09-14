# Dual-engine PDF Toolkit implementation report

## Delivered architecture

The Vite starter is replaced by one React SPA at `/pypdf/:toolId` and
`/pymupdf/:toolId`. Both engines use the clean `/api/v1` FastAPI contract, the
same owner-isolated SQLite/file store, PyMuPDF previews, and one persistent History
dialog. Backend catalogs drive categories, tools, fields, validation, and conditional
option visibility.

The exact ten-color array and stable engine indices live only in
`frontend/src/theme.js`. Action and hover colors are derived at runtime through HSL
adjustment and a WCAG 4.5:1 white-text contrast check. Auto, Light, and Dark themes
share semantic vanilla CSS.

The navbar links to `/api-check`, where pypdf and PyMuPDF each have an
independent POST test. Every case generates its own PDF, uploads it through the
shared API, performs a real operation, and displays its HTTP response and
Success/Failed result.

## Component divergence report

| Existing component | Treatment | Material difference |
| --- | --- | --- |
| `AppShell` | Refactored | Production SPA layout and overlay slot with semantic classes. |
| `Navbar` | Refactored | Hosts engine/theme controls and disables navigation while busy. |
| `Sidebar`, buttons, groups | Refactored | Catalog-driven tool navigation with propagated busy state. |
| `BodyCard` | Refactored | Structure retained; utilities replaced by `pdf-card*` classes. |
| Button family | Refactored | Contracts retained; semantic variants replace utility classes. |
| Input family | Refactored | Accessible contracts retained; shared `pdf-field*` styling. Textarea/checkbox remain native catalog fields. |
| `Dropdown` | Refactored | Existing disclosure behavior retained with vanilla styling. |
| `Dialog` | Refactored | Existing native-modal focus/Escape behavior retained. |
| `FileDropzone` | Refactored | Validation extended to HTML/any inputs; disabled while busy. |
| `FilePreview` | Refactored | Existing file/URL preview retained for private previews and outputs. |
| `FileCollection`, `FileItem` | Refactored | Grid/list/remove/reorder retained; controls honor busy state. |
| `ProcessingStatus`, `FileProgress` | Refactored | Explicit lifecycle and truthful progress behavior. |
| `ResultPanel` | Refactored | Real Download button, missing-output state, required `#result` section. |
| `HistoryDialog` | Refactored | Persisted jobs, two filters, pagination, availability, and restoration. |
| Workspace components | Reused through composition | Responsibilities are composed in `App.jsx` so one form also supports page selection and restoration without duplicate state. |
| `LoginDialog` | Not used | Login is excluded; the neutral owner cookie supplies local isolation. |
| Legacy engine preview apps | Replaced | Separate pages could not provide shared routing, state, History, or themes; their development URLs now enter the SPA. |
| `EngineSwitch` | New, permitted | Required keyboard-accessible segmented control. |
| `ThemeControl` | New, permitted | Required persisted Auto/Light/Dark selector. |

No extra production component was introduced for History filters; they live inside
`HistoryDialog` using the existing `Select`.

## Capability result

- pypdf audit: 55 functions are directly available and flattening is explicitly
  PyMuPDF-assisted. Underline, Squiggly, StrikeOut, PolyLine, and Popup remain absent.
- All prior PyMuPDF adapters remain, with local OCR, network-isolated HTML-to-PDF,
  reflowable EPUB, and conservative watermark detection/removal added.
- App-managed watermarks are tagged and exactly removable. External exact text
  removal requires confirmation; external images/vectors are detection-only.

## Verification

- Backend: 21 tests pass across both engines and the shared API.
- Frontend: lint/build pass; seven Node tests pass.
- Browser acceptance: routing, upload/preview/run, switching, History restoration,
  result focus/scroll, download availability, and dark theme were exercised against
  the live app without console errors.
