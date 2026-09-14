# PDF Toolkit component library

The production React SPA is assembled from the controlled components in this folder.
Components contain behavior and semantic `pdf-*` class names; all visual styling
lives in `styles.css`. No Tailwind compiler or utility styling is in production.

## Imports and styling

```jsx
import {
  AppShell, Navbar, Sidebar, BodyCard, FileDropzone, ResultPanel,
} from "@components";
```

`@/` maps to `frontend/src` and `@components/` maps here. Importing the barrel or
`AppShell` loads the shared stylesheet. Engine colors are never literals inside
components: `src/theme.js` validates the indexed palette, derives accessible action
colors, and supplies CSS custom properties.

## Production contracts

| Area | Components | Contract |
| --- | --- | --- |
| Layout | `AppShell`, `Navbar`, `Sidebar`, `BodyCard` | Compact navigation, tinted sidebar, responsive workspace, restrained cards. |
| Navigation | `EngineSwitch`, `ThemeControl`, `Dropdown`, `SidebarButton` | Keyboard-operable SPA controls; disabled while busy. |
| Inputs | `Input`, `Select`, `Slider`, native textarea/checkbox | Catalog-driven labels, constraints, errors, and visibility. |
| Upload | `FileDropzone`, `FileCollection`, `FilePreview` | Validation, ordered inputs, private previews, busy disabling. |
| Status | `ProcessingStatus`, `FileProgress` | Determinate progress only when measurable; otherwise indeterminate. |
| Result | `ResultPanel` | Focusable `#result`, previews, availability, authenticated button downloads. |
| History | `HistoryDialog`, `Dialog` | Filters, loading/error/empty states, cursor pages, cross-engine restoration. |
| Diagnostics | `ApiCheckPage` | Generates isolated PDF fixtures and reports the real response from one POST operation per engine. |

`App.jsx` owns bootstrapping, catalogs, SPA routes, uploads, processing, History,
restoration, downloads, and Auto/Light/Dark theme selection. Presentational
components make no network calls and never persist credentials.

## Special routes

- `/` — Redirects to `/pypdf/render`.
- `/api-check` — Runs the two self-contained production API checks (the page posts each generated fixture to:
  - `POST /api/v1/pypdf/operations/select`
  - `POST /api/v1/pymupdf/operations/rotate`
  and records those jobs in History).
- `/:engineId/:toolId` — Main toolkit workspace route (for example, `/pypdf/render`).
- `*` — Catch-all route; redirects to `/pypdf/render`.
- `/previewV1`, `/previewV1.html` — Legacy aliases that enter the production SPA workspace.

## Development and verification

Run the following checks after edits:

```powershell
npm run lint
npm run build
node --test src/theme.test.js src/components/upload/validation.test.js
```
