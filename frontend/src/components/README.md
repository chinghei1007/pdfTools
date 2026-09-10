# PDF Toolkit component library

Components are presentational and controlled by props where state is shared. They make no network calls and do not store credentials. The existing App.jsx is intentionally untouched.

## Imports and styles

```jsx
import {
  AppShell,
  Navbar,
  Sidebar,
  ToolWorkspace,
  FileDropzone,
} from "@components";
// Direct imports also work:
import { Button } from "@/components/buttons/Button";
```

`@/` points to `frontend/src/`; `@components/` points to this folder. Vite aliases apply to dev/build, not standalone Node scripts. Editor path mappings would require a root jsconfig/tsconfig change outside this task's scope.

The barrel and AppShell import styles.css. When using only direct imports, import `@components/styles.css` once. Utilities are generated with the existing Tailwind compiler by the Vite plugin, without a Preflight/global reset. Class names must be complete literals (for example `bg-red-700`, not `bg-${color}-700`). The plugin scans this component folder and reloads it when edited. If the application later adopts Tailwind globally, replace this small compiler bridge with the official Tailwind Vite plugin. Do not run both pipelines over styles.css.

The starter App.css/index.css still impose global styles. The isolated preview excludes them. When integrating the app later, review those starter styles separately.

## Preview

Run `npm run dev` in frontend, then open `/previewV1`. This separate entry exercises uploads, previews, grid/list, keyboard-accessible reordering, nested sidebar groups, dropdowns, settings, and dialogs. Authentication/processing/downloads are intentionally disabled without callbacks; no success is simulated.

## Component map and contracts

| Folder    | Exports                                | Contract                                                                                                                                                                                                                 |
| --------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| buttons   | Button, IconButton, CloseButton        | Button: variant primary/secondary/ghost/danger, size sm/md/lg, loading, disabled, native button props. IconButton requires label. Defaults to type=button.                                                               |
| inputs    | Input, Select, Slider                  | Label/hint/error are linked to the control. Input/Select accept native props. Select options: `{value,label,disabled?}`. Slider receives numeric value and calls onChange(number).                                       |
| dialogs   | Dialog                                 | Controlled open, onClose, title, description, children, footer. Native modal focus containment, Escape, backdrop dismissal, focus restoration. Content unmounts on close.                                                |
| dropdown  | Dropdown                               | label, items `{id,label,disabled?}`, value, onSelect(id). Disclosure with ordinary Tab-navigable buttons, Escape and outside dismissal. Use Select for form values.                                                      |
| sidebar   | Sidebar, SidebarButton, SidebarGroup   | title, items `{id,label,disabled?,children?}`, selectedId, onSelect(id). Groups support recursive children and defaultExpanded. Group expansion is local; selected tool belongs to the parent.                           |
| navbar    | Navbar                                 | brand, categories, categoryId, onCategoryChange, onHistory, onAccount, accountLabel.                                                                                                                                     |
| layout    | AppShell                               | Slots: navbar, sidebar, children, overlays. Responsive stacked/mobile and side-by-side/desktop layout.                                                                                                                   |
| cards     | BodyCard                               | title, description, children, footer, className. Use for upload, preview, or settings sections.                                                                                                                          |
| upload    | FileDropzone                           | accept, multiple, maxSizeBytes, disabled, onFilesSelected(File[]), onValidationError(string[]). Valid files are accepted even when other files fail. multiple=false limits each selection; parent owns total file count. |
| preview   | FilePreview                            | file (File/Blob) or url, name, mediaType, renderPdf. Local object URLs are revoked. Images preview inline; PDF embedding is opt-in; unsupported formats show a fallback. Supply trusted preview URLs only.               |
| preview   | FileItem, FileCollection               | entries `{id,file?,name?,size?,mediaType?,url?,error?,progress?}`. Stable IDs required. FileCollection: files, view grid/list, onViewChange, onRemove(id), onReorder(fromIndex,toIndex).                                 |
| preview   | ResultPanel                            | files, onDownload(entry), onReset, children. Parent handles authenticated downloading.                                                                                                                                   |
| status    | FileProgress, ProcessingStatus         | Numeric progress 0–100 or undefined for indeterminate. Status: idle/ready/reading/queued/running/succeeded/failed. Optional message.                                                                                     |
| history   | HistoryDialog                          | open, onClose, entries `{id,label,status,createdAt?}`, loading, error, onSelect(entry).                                                                                                                                  |
| auth      | LoginDialog                            | open, onClose, onSubmit({username,password}), loading, error, optional onRegister/onForgotPassword. Parent owns async request and errors; password is cleared when closed.                                               |
| workspace | ToolWorkspace, ToolHeader, ToolOptions | Workspace slots: upload, preview, settings, result; title, description, status, progress, message, onRun, canRun, actionLabel. ToolOptions disables settings while busy. Parent disables upload/remove when needed.      |

Input file validation is a UX aid, not a replacement for backend validation. Never send arbitrary filesystem paths from these components. File previews do not perform OCR, rasterize PDF pages, or convert documents.

## Verification

`npm run lint` and `npm run build` validate the existing app. To validate the entire component library (the starter app does not import it), use a separate Vite build with `src/components/index.js` as its library entry. The upload validator tests run with `node --test src/components/upload/validation.test.js`.

The /previewV1 shortcut (also /previewV1.html) is configured through Vite development middleware and serves examples/previewV1.html. It is a local dev route, not a production application route or a React Router route.

