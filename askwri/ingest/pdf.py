"""Read a PDF with PyMuPDF's layout model into ordered text and heading blocks."""

import html
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from askwri.ingest.text import comparable, missing_words

# Layout classes that carry body text. Tables and pictures get their own chunk kinds later.
TEXT_CLASSES = {"text", "list-item", "footnote", "formula", "caption"}
HEADING_CLASSES = {"title", "section-header"}


@dataclass(frozen=True)
class Block:
    """One layout region of a page, in reading order, as plain text."""

    page: int  # 1-based position in the PDF file
    heading_level: int  # 0 for body text, 1 for "#", 2 for "##", ...
    text: str


@dataclass(frozen=True)
class ParsedPdf:
    """What the chunker needs from a PDF: its metadata title and its blocks in reading order."""

    title: str
    blocks: list[Block]


def parse_pdf(path: Path) -> ParsedPdf:
    """Parse a PDF into text and heading blocks.

    The layout model decides the regions, their classes and their reading order. Page headers,
    footers, pictures and tables are skipped. OCR is off: a page without a text layer yields
    no blocks, so every passage stays checkable against the PDF's own text.
    """
    with pymupdf.open(path) as doc:
        pages = doc.to_markdown(
            page_chunks=True, header=False, footer=False, use_ocr=False, show_progress=False
        )
        title = (doc.metadata or {}).get("title", "").strip()
        blocks = []
        for chunk in pages:
            page = doc[chunk["metadata"]["page_number"] - 1]
            page_text = page.get_text()
            for box in sorted(chunk["page_boxes"], key=lambda box: box["index"]):
                if box["class"] not in TEXT_CLASSES | HEADING_CLASSES:
                    continue
                start, stop = box["pos"]
                markdown = chunk["text"][start:stop].strip()
                text = region_text(page, page_text, box["bbox"], plain_text(markdown))
                if not text:
                    continue
                level = 0
                if box["class"] in HEADING_CLASSES:
                    level = len(markdown) - len(markdown.lstrip("#")) or 1
                blocks.append(Block(page=page.number + 1, heading_level=level, text=text))
    return ParsedPdf(title=title, blocks=blocks)


def region_text(
    page: pymupdf.Page, page_text: str, bbox: tuple[float, float, float, float], layout_text: str
) -> str:
    """Pick the region's text: the layout model's, unless the PDF's own text layer is better.

    The layout Markdown sometimes misplaces ligatures ("frst", "tarifs") or interleaves a pull
    quote into a paragraph. The text layer read from the same region has the words verbatim.
    It wins when it is a verbatim run of the page and the layout text is not, or when the
    layout text has words that are not on the page at all.
    """
    page_run = comparable(page_text)
    if comparable(layout_text) in page_run:
        return layout_text
    region = pymupdf.Rect(bbox) + (-2, -2, 2, 2)  # layout boxes can clip edge characters
    layer_text = plain_text(page.get_text("text", clip=region, flags=pymupdf.TEXT_DEHYPHENATE))
    complete = len(comparable(layer_text)) >= 0.95 * len(comparable(layout_text))
    if complete and comparable(layer_text) in page_run:
        return layer_text
    if missing_words(layout_text, page_text):
        return layer_text
    return layout_text


def plain_text(markdown: str) -> str:
    """Strip the Markdown and HTML that PyMuPDF adds, so the text reads as it does in the PDF."""
    text = re.sub(r"<br\s*/?>", " ", markdown)
    text = re.sub(r"_{3,}|\.{4,}|…{2,}", " ", text)  # blank form lines and dot leaders
    text = re.sub(r"</?[a-z]+>", "", text)
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"(?<!\w)_|_(?!\w)", "", text)
    return " ".join(html.unescape(text).split())
