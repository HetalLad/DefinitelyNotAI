"""Document labels: WRI's own topic, type, authors, date and tags, read from its wri.org page."""

import html
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pymupdf

from askwri.ingest.wri_site import WriSite

TOPICS = (
    "Business",
    "Cities",
    "Climate",
    "Economics",
    "Energy",
    "Equity",
    "Finance",
    "Food",
    "Forests",
    "Freshwater",
    "Ocean",
)
# Site topic names that differ from the 11 menu topics. Any other value is an error.
SITE_TOPICS = {**{topic: topic for topic in TOPICS}, "Equity & Governance": "Equity"}
FRONT_PAGES = 5  # a document's own DOI and date sit in the first pages; later DOIs are cited
# PDF text sometimes breaks a DOI with a space after the slash: "doi.org/10.46830/ wrirpt.24.1"
WRI_DOI = re.compile(r"10\.46830/ ?[A-Za-z0-9.\-]*[A-Za-z0-9]")
CITATION_MARKER = re.compile(r"suggested citation|available online at", re.IGNORECASE)
DOI_REACH = 600  # characters after a citation marker in which its DOI must start


@dataclass(frozen=True)
class DocumentLabels:
    """One document's labels. Everything but the source and title is empty when no page exists."""

    label_source: str  # "wri.org", or "no page" (the citation then falls back to the stored PDF)
    title: str  # the wri.org page's title, else the PDF's
    doi: str | None  # the document's own WRI DOI as printed in the PDF
    link: str | None  # the wri.org page, checked to resolve
    page_match: str | None  # "doi" or "title"
    topic: str | None  # one of TOPICS
    wri_type: str | None
    authors: tuple[str, ...]
    published: str | None  # ISO date
    tags: tuple[str, ...]  # secondary tags: feed search filters, never counts


def label_document(pdf_path: Path, title: str, site: WriSite | None) -> DocumentLabels:
    """Find the document's wri.org page and read its labels; without a page, say so.

    With no site, nothing is looked up and the result is "no page". A label the page lacks is
    left empty, never an error.
    """
    front_text = _front_text(pdf_path)
    doi = own_doi(front_text)
    page = site.find_page(title, doi) if site else None
    if page is None:
        return DocumentLabels(
            label_source="no page",
            title=title,
            doi=doi,
            link=None,
            page_match=None,
            topic=None,
            wri_type=None,
            authors=(),
            published=None,
            tags=(),
        )
    meta = page.meta
    topic, tags = _topic_and_tags(meta)
    return DocumentLabels(
        label_source="wri.org",
        title=page.title,
        doi=doi,
        link=page.url,
        page_match=page.match,
        topic=topic,
        wri_type=_first(meta, "wri_type"),
        authors=tuple(meta.get("citation_author", [])),
        published=_published(meta),
        tags=tags,
    )


def own_doi(front_text: str) -> str | None:
    """The WRI DOI in the document's suggested-citation block, else None.

    Reports also print the DOIs of works they cite, and some of those resolve to translations,
    so only a DOI that follows "Suggested citation" or "Available online at" counts.
    """
    for marker in CITATION_MARKER.finditer(front_text):
        if doi := WRI_DOI.search(front_text, marker.end(), marker.end() + DOI_REACH):
            return doi.group(0).replace(" ", "")
    return None


def catalog_row(doc_id: str, pdf_file: str, labels: DocumentLabels) -> dict:
    """One catalog row: the document's labels, plus the stored PDF a citation falls back to."""
    return {"doc_id": doc_id, "pdf_file": pdf_file, **asdict(labels)}


def chunk_label_fields(labels: DocumentLabels) -> dict:
    """The label fields every chunk of the document carries, for filtering at search time."""
    return {
        "label_source": labels.label_source,
        "link": labels.link,
        "year": int(labels.published[:4]) if labels.published else None,
        "topic": labels.topic,
        "wri_type": labels.wri_type,
        "tags": labels.tags,
    }


def _front_text(pdf_path: Path) -> str:
    with pymupdf.open(pdf_path) as doc:
        return " ".join(" ".join(page.get_text().split()) for page in list(doc)[:FRONT_PAGES])


def _first(meta: dict[str, list[str]], key: str) -> str | None:
    return meta[key][0] if meta.get(key) else None


def _topic_and_tags(meta: dict[str, list[str]]) -> tuple[str | None, tuple[str, ...]]:
    """The main topic and the secondary tags.

    The topic is `wri_topic` when it maps onto the 11 topics, else the first `article:tag` that
    is one of them, else None (the labeler of a later ticket fills it). An off-list
    `wri_topic` such as the region "Africa" is kept as a tag.
    """
    tags = list(meta.get("article:tag", []))
    site_topic = html.unescape(_first(meta, "wri_topic") or "")
    topic = SITE_TOPICS.get(site_topic)
    if topic is None and site_topic and site_topic not in tags:
        tags.append(site_topic)
    if topic is None:
        topic = next((SITE_TOPICS[tag] for tag in tags if tag in SITE_TOPICS), None)
    return topic, tuple(tags)


def _published(meta: dict[str, list[str]]) -> str | None:
    """The publication date as YYYY-MM-DD, or None.

    `wri_published` ("June 10 2025") is unambiguous. Without it, `citation_publication_date`
    is read as YYYY-DD-MM, the format the site writes it in.
    """
    try:
        if long_date := _first(meta, "wri_published"):
            return datetime.strptime(long_date, "%B %d %Y").date().isoformat()
        if stamp := _first(meta, "citation_publication_date"):
            year, day, month = (int(part) for part in stamp.split("-"))
            return date(year, month, day).isoformat()
    except ValueError:
        return None
    return None
