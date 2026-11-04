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

    With no site, nothing is looked up and the result is "no page". Raises ValueError for a
    topic outside the 11 or a publication date that nothing can settle.
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
    return DocumentLabels(
        label_source="wri.org",
        title=page.title,
        doi=doi,
        link=page.url,
        page_match=page.match,
        topic=_topic(meta, page.url),
        wri_type=_first(meta, "wri_type"),
        authors=tuple(meta.get("citation_author", [])),
        published=_published(meta, front_text),
        tags=tuple(meta.get("article:tag", [])),
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


def _topic(meta: dict[str, list[str]], url: str) -> str | None:
    site_topic = _first(meta, "wri_topic")
    if site_topic is None:
        return None
    try:
        return SITE_TOPICS[html.unescape(site_topic)]
    except KeyError:
        raise ValueError(f"{url}: wri_topic {site_topic!r} is not one of the 11 topics") from None


def _published(meta: dict[str, list[str]], front_text: str) -> str | None:
    """The publication date as YYYY-MM-DD.

    The site writes `citation_publication_date` as YYYY-DD-MM. A day over 12 settles it. When
    both readings are real dates, the one whose month and year the PDF prints wins; failing
    that, the page's own `wri_published` ("June 10 2025") decides.
    """
    stamp = _first(meta, "citation_publication_date")
    if stamp is None:
        return None
    year, first, second = (int(part) for part in stamp.split("-"))
    candidates: list[date] = []
    for month, day in ((second, first), (first, second)):
        try:
            reading = date(year, month, day)
        except ValueError:
            continue
        if reading not in candidates:
            candidates.append(reading)
    if len(candidates) > 1:
        candidates = [d for d in candidates if _printed_in(d, front_text)] or candidates
    if len(candidates) > 1 and (long_date := _first(meta, "wri_published")):
        written = datetime.strptime(long_date, "%B %d %Y").date()
        candidates = [d for d in candidates if d == written]
    if len(candidates) != 1:
        raise ValueError(f"publication date {stamp} is ambiguous and nothing settles it")
    return candidates[0].isoformat()


def _printed_in(day: date, front_text: str) -> bool:
    return bool(re.search(rf"{day:%B}\W+(?:\d{{1,2}}\W+)?{day.year}", front_text, re.IGNORECASE))
