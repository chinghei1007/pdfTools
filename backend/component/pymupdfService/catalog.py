"""User-facing operations plus a read-only inventory of the installed API."""
import inspect
import pymupdf


def field(key, label, kind="text", default="", choices=None):
    return dict(key=key, label=label, kind=kind, default=default, choices=choices)


PAGES = field("pages", "Pages / ranges (1-based, e.g. 1-3,5,4; blank = all, max 30)")
TEXT = field("text", "Text", default="Sample text")
RECT = field("rect", "Rectangle x0,y0,x1,y1 (PDF points)", default="30,30,250,100")
TOOLS = []


def add(id, label, category, fields=(), input="pdf", multiple=False):
    TOOLS.append(dict(id=id, label=label, category=category, fields=list(fields), input=input, multiple=multiple))


add("image-to-pdf", "Images to PDF", "Convert", input="image", multiple=True)
add("render", "PDF pages to images", "Convert", [PAGES, field("format", "Image format", "select", "png", ["png", "jpg"]), field("dpi", "DPI (36–144)", "number", 96)])
add("svg", "Pages to SVG", "Convert", [PAGES])
add("text", "Extract text / HTML / XML", "Extract", [PAGES, field("format", "Text format", "select", "text", ["text", "html", "xhtml", "xml", "json"])])
for id, label in [("images", "Embedded images"), ("tables", "Tables (JSON)"), ("annotations", "Annotations (JSON)"), ("links", "Links (JSON)"), ("drawings", "Vector drawings (JSON)"), ("widgets", "Form fields (JSON)")]:
    add(id, label, "Extract", [PAGES])
for id, label in [("metadata", "Document metadata"), ("toc", "Bookmarks / outline"), ("attachments", "Embedded attachments")]:
    add(id, label, "Inspect")
add("search", "Search text", "Inspect", [PAGES, TEXT])
add("merge", "Merge PDFs", "Pages", multiple=True)
add("select", "Select / reorder pages", "Pages", [PAGES])
add("split", "Split into individual PDFs", "Pages", [PAGES])
add("rotate", "Rotate pages", "Pages", [PAGES, field("angle", "Clockwise degrees", "select", "90", ["90", "180", "270"])])
add("crop", "Crop pages", "Pages", [PAGES, RECT])
add("compress", "Optimize PDF storage", "Edit")
add("watermark", "Add text watermark", "Edit", [PAGES, TEXT])
add("highlight", "Highlight matching text", "Edit", [PAGES, TEXT])
add("redact", "Redact rectangle", "Edit", [PAGES, RECT])
add("note", "Add sticky note", "Edit", [PAGES, TEXT])
add("set-metadata", "Set title and author", "Edit", [field("title", "Title"), field("author", "Author")])
add("flatten", "Flatten annotations and forms", "Edit")
add("encrypt", "Password protect PDF", "Security", [field("password", "New PDF password", "password")])
add("decrypt", "Save unlocked copy", "Security")


def library_catalog():
    """Do not expose dynamic invocation: methods can access disk/native state."""
    result = []
    for name in sorted(dir(pymupdf)):
        if name.startswith("_"):
            continue
        value = getattr(pymupdf, name)
        if not callable(value):
            continue
        members = []
        if inspect.isclass(value):
            members = [member for member in dir(value) if not member.startswith("_")]
        result.append(dict(name=name, members=members, exposed=False))
    return dict(version=pymupdf.VersionBind, symbols=result, tools=TOOLS)
