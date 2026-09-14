"""Allowlisted, bounded document operations. Page numbers in APIs are 1-based."""
import io
import html
import json
import zipfile
from contextlib import ExitStack
import pymupdf
from .catalog import TOOLS


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, default=str, indent=2).encode()


def bundle(items):
    if len(items) == 1:
        return items[0]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data, _ in items:
            archive.writestr(name, data)
    return "results.zip", stream.getvalue(), "application/zip"


def open_document(path, password=""):
    doc = pymupdf.open(path)
    if doc.needs_pass and not doc.authenticate(password):
        doc.close()
        raise ValueError("This PDF requires a valid password.")
    if not 0 < doc.page_count <= 1000:
        doc.close()
        raise ValueError("Documents must have 1–1000 pages.")
    return doc


def page_indices(doc, value):
    return parse_pages(value, doc.page_count)


def parse_pages(value, count):
    """Inclusive 1-based ranges and explicit order, bounded before expansion."""
    try:
        pages = []
        for token in value.split(',') if value.strip() else [f'1-{count}']:
            parts = token.strip().split('-')
            if len(parts) == 1:
                start = end = int(parts[0])
            elif len(parts) == 2:
                start, end = map(int, parts)
            else: raise ValueError()
            if not 1 <= start <= end <= count or len(pages) + end - start + 1 > 30:
                raise ValueError()
            pages.extend(range(start - 1, end))
    except (ValueError, AttributeError):
        raise ValueError("Select up to 30 valid pages using 1-based numbers/ranges, e.g. 1-3,5,4.") from None
    return pages


def rectangle(value, page):
    try:
        values = [float(x) for x in value.split(",")]
        if len(values) != 4:
            raise ValueError()
        rect = pymupdf.Rect(values)
        if rect.is_empty or rect.is_infinite or not page.rect.contains(rect):
            raise ValueError()
        return rect
    except (ValueError, TypeError):
        raise ValueError("Rectangle must be finite, nonempty and inside the page.") from None


def preview(path, password, page=1):
    with open_document(path, password) as doc:
        if not 1 <= page <= doc.page_count:
            raise ValueError("Page does not exist.")
        p = doc[page - 1]
        scale = min(600 / max(p.rect.width, p.rect.height), 1)
        pix = p.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        return pix.tobytes("png"), pix.width, pix.height


def process(tool_id, paths, options, passwords):
    tool = next((t for t in TOOLS if t["id"] == tool_id), None)
    if not tool:
        raise ValueError("Unknown operation.")
    allowed = {f["key"]: f for f in tool["fields"]}
    if set(options) - set(allowed):
        raise ValueError("Unsupported option for this operation.")
    opts = {key: options.get(key, f["default"]) for key, f in allowed.items()}
    for key, f in allowed.items():
        if f["choices"] and opts[key] not in f["choices"]:
            raise ValueError(f"Invalid {key}.")
    if tool_id == "html-to-pdf":
        if len(paths) > 1:
            raise ValueError("Provide one HTML file or pasted HTML, not both.")
        source = str(opts.get("html", "")).strip()
        if paths:
            if source:
                raise ValueError("Use either an HTML file or pasted HTML, not both.")
            source = paths[0][1].read_text(encoding="utf-8", errors="replace")
        if not source:
            raise ValueError("Upload an HTML file or paste HTML content.")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as runtime:
                browser = runtime.chromium.launch(headless=True)
                page = browser.new_page()
                page.route("**/*", lambda route: route.abort() if route.request.url.startswith(("http://", "https://")) else route.continue_())
                page.set_content(source, wait_until="domcontentloaded")
                result = page.pdf(print_background=True, format="A4")
                browser.close()
        except Exception as exc:
            raise ValueError("HTML rendering is unavailable. Install the Playwright Chromium browser.") from exc
        return "document.pdf", result, "application/pdf"
    if not paths or len(paths) > 10 or (not tool["multiple"] and len(paths) != 1):
        raise ValueError("Invalid number of input files.")
    with ExitStack() as stack:
        docs = [stack.enter_context(open_document(path, passwords.get(id, ""))) for id, path in paths]
        doc = docs[0]
        if tool["input"] == "pdf" and any(not d.is_pdf for d in docs):
            raise ValueError("This tool only accepts PDFs.")
        if tool["input"] == "image" and any(d.is_pdf or d.page_count != 1 for d in docs):
            raise ValueError("This tool only accepts images.")
        if tool_id in ("merge", "image-to-pdf"):
            out = stack.enter_context(pymupdf.open())
            for source in docs:
                if source.is_pdf:
                    out.insert_pdf(source)
                else:
                    converted = stack.enter_context(pymupdf.open("pdf", source.convert_to_pdf()))
                    out.insert_pdf(converted)
            return "combined.pdf", out.tobytes(garbage=4, deflate=True), "application/pdf"
        indices = page_indices(doc, opts.get("pages", "")) if "pages" in allowed else []
        pages = [doc[i] for i in indices]
        if tool_id == "ocr":
            language = str(opts["language"]).strip() or "eng"
            if not re_language(language):
                raise ValueError("Use installed Tesseract language codes such as eng or eng+deu.")
            if opts["format"] == "text":
                extracted = []
                for index, page in zip(indices, pages):
                    existing = page.get_text()
                    if existing.strip():
                        value = existing
                    else:
                        text_page = page.get_textpage_ocr(language=language, full=True)
                        value = page.get_text(textpage=text_page)
                    extracted.append(f"--- Page {index + 1} ---\n{value}")
                return "ocr.txt", "\n\n".join(extracted).encode(), "text/plain"
            output = stack.enter_context(pymupdf.open())
            for page in pages:
                if page.get_text().strip():
                    output.insert_pdf(doc, from_page=page.number, to_page=page.number)
                else:
                    rendered = page.get_pixmap(dpi=150, alpha=False).pdfocr_tobytes(language=language)
                    part = stack.enter_context(pymupdf.open("pdf", rendered))
                    output.insert_pdf(part)
            return "searchable.pdf", output.tobytes(garbage=4, deflate=True), "application/pdf"
        if tool_id == "pdf-to-epub":
            try:
                from ebooklib import epub
            except ImportError as exc:
                raise ValueError("EPUB export requires EbookLib.") from exc
            book = epub.EpubBook()
            book.set_identifier("pdf-toolkit-export")
            book.set_title(doc.metadata.get("title") or "PDF export")
            book.set_language("en")
            chapters = []
            for position, (index, page) in enumerate(zip(indices, pages), 1):
                chapter = epub.EpubHtml(title=f"Page {index + 1}", file_name=f"page-{position}.xhtml", lang="en")
                chapter.content = f"<h1>Page {index + 1}</h1><pre>{html.escape(page.get_text())}</pre>"
                book.add_item(chapter)
                chapters.append(chapter)
            book.toc = tuple(chapters)
            book.spine = ["nav", *chapters]
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            target = io.BytesIO()
            epub.write_epub(target, book)
            return "document.epub", target.getvalue(), "application/epub+zip"
        if tool_id in ("render", "svg", "text", "split"):
            items = []
            for index, page in zip(indices, pages):
                name = f"page-{index + 1}"
                if tool_id == "render":
                    dpi = int(opts["dpi"])
                    if not 36 <= dpi <= 300 or page.rect.width * page.rect.height * (dpi / 72) ** 2 > 12_000_000:
                        raise ValueError("DPI must be 36–300; rendered page must be under 12 megapixels.")
                    fmt = opts["format"]
                    items.append((f"{name}.{fmt}", page.get_pixmap(dpi=dpi, alpha=False).tobytes("jpeg" if fmt == "jpg" else fmt), "image/jpeg" if fmt == "jpg" else "image/png"))
                elif tool_id == "svg":
                    items.append((f"{name}.svg", page.get_svg_image().encode(), "image/svg+xml"))
                elif tool_id == "text":
                    fmt = opts["format"]
                    items.append((f"{name}.{'txt' if fmt == 'text' else fmt}", page.get_text(fmt).encode(), "text/plain"))
                else:
                    with pymupdf.open() as part:
                        part.insert_pdf(doc, from_page=index, to_page=index)
                        items.append((f"{name}.pdf", part.tobytes(), "application/pdf"))
            return bundle(items)
        data = None
        if tool_id == "metadata": data = doc.metadata
        elif tool_id == "toc": data = doc.get_toc()
        elif tool_id == "attachments":
            return bundle([(f"attachment-{i}.bin", doc.embfile_get(i), "application/octet-stream") for i in range(doc.embfile_count())])
        elif tool_id == "images":
            items, seen = [], set()
            for page in pages:
                for image in page.get_images():
                    if image[0] in seen: continue
                    seen.add(image[0])
                    extracted = doc.extract_image(image[0])
                    if extracted: items.append((f"image-{image[0]}.{extracted['ext']}", extracted["image"], "application/octet-stream"))
            return bundle(items)
        elif tool_id in ("tables", "annotations", "links", "widgets", "drawings", "search"):
            data = []
            for index, page in zip(indices, pages):
                if tool_id == "tables": value = [table.extract() for table in page.find_tables().tables]
                elif tool_id == "annotations": value = [dict(a.info, rect=list(a.rect), type=a.type) for a in (page.annots() or [])]
                elif tool_id == "links": value = page.get_links()
                elif tool_id == "widgets": value = [dict(name=w.field_name, value=w.field_value, type=w.field_type_string) for w in (page.widgets() or [])]
                elif tool_id == "drawings": value = page.get_drawings()
                else: value = [list(r) for r in page.search_for(str(opts["text"]))]
                data.append(dict(page=index + 1, result=value))
        if tool_id == "remove-watermark" and opts["mode"] == "detect":
            candidates = []
            for index, page in zip(indices, pages):
                app_marks = [a for a in (page.annots() or []) if a.info.get("subject") == "pdf-toolkit-watermark"]
                if app_marks:
                    candidates.append(dict(page=index + 1, type="app-managed", count=len(app_marks), reliablyRemovable=True))
                if page.get_text().strip():
                    candidates.append(dict(page=index + 1, type="text", reliablyRemovable=False))
                if page.get_images():
                    candidates.append(dict(page=index + 1, type="image", reliablyRemovable=False))
                if page.get_drawings():
                    candidates.append(dict(page=index + 1, type="vector/SVG-like", reliablyRemovable=False))
            return "watermark-detection.json", json_bytes(candidates), "application/json"
        if data is not None:
            return f"{tool_id}.json", json_bytes(data), "application/json"
        if tool_id == "select": doc.select(indices)
        elif tool_id == "set-metadata": doc.set_metadata({**doc.metadata, "title": str(opts["title"]), "author": str(opts["author"])})
        elif tool_id == "flatten": doc.bake()
        for page in pages:
            if tool_id == "rotate": page.set_rotation((page.rotation + int(opts["angle"])) % 360)
            elif tool_id == "crop": page.set_cropbox(rectangle(opts["rect"], page))
            elif tool_id == "watermark":
                rect = pymupdf.Rect(30, max(30, page.rect.height / 2 - 35), page.rect.width - 30, page.rect.height / 2 + 35)
                mark = page.add_freetext_annot(rect, str(opts["text"]), fontsize=24, text_color=(0.45, 0.45, 0.45), align=pymupdf.TEXT_ALIGN_CENTER)
                mark.set_info(subject="pdf-toolkit-watermark", content=str(opts["text"]), title="PDF Toolkit")
                mark.set_opacity(0.35)
                mark.update()
            elif tool_id == "remove-watermark":
                if opts["mode"] == "remove-app":
                    for annotation in list(page.annots() or []):
                        if annotation.info.get("subject") == "pdf-toolkit-watermark":
                            page.delete_annot(annotation)
                elif opts["mode"] == "remove-text":
                    if opts.get("confirm") not in (True, "true", "1", 1):
                        raise ValueError("Confirm destructive external text removal.")
                    target = str(opts.get("text", "")).strip()
                    if not target:
                        raise ValueError("Provide the exact watermark text to remove.")
                    matches = page.search_for(target)
                    for match in matches:
                        page.add_redact_annot(match, fill=(1, 1, 1))
                    if matches:
                        page.apply_redactions()
            elif tool_id == "note": page.add_text_annot((30, 30), str(opts["text"]))
            elif tool_id == "highlight":
                for rect in page.search_for(str(opts["text"])): page.add_highlight_annot(rect)
            elif tool_id == "redact":
                page.add_redact_annot(rectangle(opts["rect"], page), fill=(0, 0, 0))
                page.apply_redactions()
        save = dict(garbage=4, deflate=True)
        if tool_id == "encrypt":
            password = str(opts["password"])
            if not 8 <= len(password) <= 40: raise ValueError("Use a PDF password of 8–40 characters.")
            save.update(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
        return f"{tool_id}.pdf", doc.tobytes(**save), "application/pdf"


def re_language(value):
    import re
    return bool(re.fullmatch(r"[A-Za-z0-9_]+(?:\+[A-Za-z0-9_]+)*", value))
