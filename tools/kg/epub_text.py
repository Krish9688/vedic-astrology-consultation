# EPUB reader for add_book.py (standard library only): one "page" per non-empty spine document, in OPF spine order.
# Page numbers are therefore "epub section" numbers (stable for a given file), not printed pages.
import posixpath, re, zipfile
from html.parser import HTMLParser
from urllib.parse import unquote
from xml.etree import ElementTree as ET

BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "section", "pre"}
HEADS = {"h1", "h2", "h3"}


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.title, self._skip, self._head = [], "", 0, False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head"):
            self._skip += 1
        if tag in BLOCK:
            self.out.append("\n")
        if tag in HEADS and not self.title:
            self._head = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head"):
            self._skip = max(0, self._skip - 1)
        if tag in BLOCK:
            self.out.append("\n")
        if tag in HEADS:
            self._head = False

    def handle_data(self, data):
        if self._skip:
            return
        self.out.append(data)
        if self._head and data.strip():
            self.title = (self.title + " " + data.strip()).strip()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def sections(path):
    """[(title, text)] for every non-empty spine document of the EPUB, in reading order."""
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("META-INF/container.xml"))
    opf = next(e.get("full-path") for e in root.iter() if _local(e.tag) == "rootfile")
    base = posixpath.dirname(opf)
    pkg = ET.fromstring(z.read(opf))
    manifest = {e.get("id"): e.get("href") for e in pkg.iter() if _local(e.tag) == "item"}
    names = set(z.namelist())
    out = []
    for e in pkg.iter():
        if _local(e.tag) != "itemref" or e.get("idref") not in manifest:
            continue
        name = posixpath.normpath(posixpath.join(base, unquote(manifest[e.get("idref")]))).lstrip("/")
        if name not in names or not name.lower().endswith((".xhtml", ".html", ".htm", ".xml")):
            continue
        p = _Text()
        p.feed(z.read(name).decode("utf-8", errors="replace"))
        text = re.sub(r"[ \t\r\f\v]+", " ", "".join(p.out))
        text = re.sub(r" ?\n ?", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            out.append((p.title, text))
    return out
