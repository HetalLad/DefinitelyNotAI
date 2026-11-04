"""Cut parsed PDF blocks into section-bounded, size-banded text chunks with stable IDs."""

import math
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, replace

from askwri.ingest.pages import PrintedPage
from askwri.ingest.pdf import Block

# The size band, at about 4 characters per token: roughly 100 to 500 tokens. Shorter chunks
# embed as little more than their address; longer ones blur several ideas into one vector.
# A starting point, to be tuned against the evaluation question set.
MIN_CHUNK_CHARS = 400
MAX_CHUNK_CHARS = 2000
SEPARATOR = " › "

SENTENCE_BREAK = re.compile(r"[.!?][\"')\]”’]*\s+")
OPENING_QUOTES = "\"'([“‘"
# Words that end in a period without ending the sentence. Single letters ("U.S.", "e.g.") are
# handled separately. Erring this way only makes a sentence longer, never cuts one in two.
ABBREVIATIONS = {
    *("al", "cf", "ca", "co", "corp", "dept", "dr", "ed", "eds", "etc", "fig", "figs", "inc"),
    *("jr", "ltd", "mr", "mrs", "ms", "no", "nos", "p", "pp", "prof", "sr", "st", "vol", "vs"),
}


@dataclass(frozen=True)
class Chunk:
    """One citable passage and everything a citation needs."""

    chunk_id: str  # "<doc_id>#p<pdf_page>-<position on page>", identical across reruns
    seq: int  # position in the document's chunk order: 1-based, contiguous, identical across reruns
    doc_id: str
    doc_title: str
    pdf_page: int  # page where the chunk starts, position in the file
    pdf_page_end: int  # page where it ends; differs from pdf_page when it crosses a page break
    printed_page: str  # number printed on the start page: "iv", "12"; the PDF page if none found
    printed_page_end: str
    printed_page_fallback: bool  # True when no printed number was found: the PDF page stands in
    section: str  # section path, e.g. "Supply risks › Lithium"
    kind: str
    text: str  # passage text; paragraphs separated by blank lines
    quotable: bool = True  # False when the audit found the words re-ordered against the PDF
    # The document's labels, copied onto every chunk so retrieval can filter on them.
    label_source: str = "no page"  # "wri.org", or "no page" (the citation then cites the PDF)
    link: str | None = None
    year: int | None = None
    topic: str | None = None
    wri_type: str | None = None
    tags: tuple[str, ...] = ()

    @property
    def address(self) -> str:
        """Where the passage sits: document title › section path."""
        return SEPARATOR.join(part for part in (self.doc_title, self.section) if part)

    @property
    def indexed_text(self) -> str:
        """The text that is embedded and searched: address first, so the passage stands alone."""
        return f"{self.address}\n\n{self.text}"


def build_chunks(
    doc_id: str, doc_title: str, blocks: list[Block], printed_pages: list[PrintedPage]
) -> list[Chunk]:
    """Group body blocks into chunks of MIN_CHUNK_CHARS to MAX_CHUNK_CHARS, numbered by `seq`.

    Chunks never cross a heading but may cross a page break, then recording both pages.
    Headings update the section path; a heading repeating the document title is not part of
    it. Short blocks join their neighbours within the section, a block over the maximum is
    cut at sentence boundaries, and a section whose whole text is short stays one short chunk.
    """
    chunks: list[Chunk] = []
    per_start_page = Counter()
    for section, body in _sections(blocks, doc_title):
        for group in _group_section(body):
            start, end = group[0].page, group[-1].page
            per_start_page[start] += 1
            first, last = printed_pages[start - 1], printed_pages[end - 1]
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}#p{start}-{per_start_page[start]}",
                    seq=len(chunks) + 1,
                    doc_id=doc_id,
                    doc_title=doc_title,
                    pdf_page=start,
                    pdf_page_end=end,
                    printed_page=first.label,
                    printed_page_end=last.label,
                    printed_page_fallback=first.fallback or last.fallback,
                    section=section,
                    kind="source_text",
                    text=_joined(group),
                )
            )
    return chunks


def _sections(blocks: list[Block], doc_title: str) -> Iterator[tuple[str, list[Block]]]:
    """Each run of body blocks between headings, with its section path."""
    path: list[tuple[int, str]] = []  # (heading level, heading text), outermost first
    body: list[Block] = []
    for block in blocks:
        if not block.heading_level:
            body.append(block)
            continue
        if body:
            yield SEPARATOR.join(text for _, text in path), body
            body = []
        if block.text.casefold() != doc_title.casefold():
            while path and path[-1][0] >= block.heading_level:
                path.pop()
            path.append((block.heading_level, block.text))
    if body:
        yield SEPARATOR.join(text for _, text in path), body


def _group_section(body: list[Block]) -> list[list[Block]]:
    """Split a section's blocks into chunk-sized groups, keeping them in reading order."""
    pieces = [piece for block in body for piece in _split_long_block(block)]
    groups: list[list[Block]] = []
    for piece in pieces:
        if groups and len(_joined([*groups[-1], piece])) <= MAX_CHUNK_CHARS:
            groups[-1].append(piece)
        else:
            groups.append([piece])
    return _lengthen_last_group(groups)


def _lengthen_last_group(groups: list[list[Block]]) -> list[list[Block]]:
    """Fix a too-short last group by re-dividing the last two as evenly as whole blocks allow.

    Greedy grouping leaves a short tail whenever it did not fit in the group before it.
    If no division puts both parts in the size band, the tail stays short.
    """
    if len(groups) < 2 or len(_joined(groups[-1])) >= MIN_CHUNK_CHARS:
        return groups
    blocks = groups[-2] + groups[-1]
    sizes = {i: (len(_joined(blocks[:i])), len(_joined(blocks[i:]))) for i in range(1, len(blocks))}
    fits = [
        i for i, size in sizes.items() if all(MIN_CHUNK_CHARS <= n <= MAX_CHUNK_CHARS for n in size)
    ]
    if not fits:
        return groups
    cut = min(fits, key=lambda i: abs(sizes[i][0] - sizes[i][1]))
    return [*groups[:-2], blocks[:cut], blocks[cut:]]


def _split_long_block(block: Block) -> list[Block]:
    """The block itself, or when it is over the maximum, pieces cut at sentence boundaries.

    Pieces are as even as sentences allow, so a block just over the maximum gives two
    half-size pieces rather than a full one and a stub. A single sentence is never cut.
    """
    if len(block.text) <= MAX_CHUNK_CHARS:
        return [block]
    target = len(block.text) / math.ceil(len(block.text) / MAX_CHUNK_CHARS)
    pieces: list[str] = []
    size = 0
    for sentence in _sentences(block.text):
        grown = size + len(sentence)
        # Cut before a sentence that would land the piece further from the target size than now.
        if pieces and (grown > MAX_CHUNK_CHARS or grown - target > target - size):
            pieces.append(sentence)
            size = len(sentence)
        elif pieces:
            pieces[-1] += f" {sentence}"
            size = grown + 1
        else:
            pieces.append(sentence)
            size = len(sentence)
    return [replace(block, text=piece) for piece in pieces]


def _sentences(text: str) -> list[str]:
    """Split text after a period, "!" or "?" that is followed by a capital letter.

    A period after an abbreviation or single letter ("Fig.", "U.S.", "e.g.") is not a break,
    and neither is one inside a number ("3.5") or before a lowercase word or a digit.
    """
    sentences, start = [], 0
    for match in SENTENCE_BREAK.finditer(text):
        word = text[start : match.start()].split()[-1:]
        if text[match.start()] == "." and word and _is_abbreviation(word[0]):
            continue
        if not text[match.end() :].lstrip(OPENING_QUOTES)[:1].isupper():
            continue
        sentences.append(text[start : match.end()].strip())
        start = match.end()
    sentences.append(text[start:].strip())
    return sentences


def _is_abbreviation(word: str) -> bool:
    word = word.lstrip(OPENING_QUOTES).casefold()
    return word in ABBREVIATIONS or re.fullmatch(r"(?:\w\.)*\w", word) is not None


def _joined(group: list[Block]) -> str:
    return "\n\n".join(block.text for block in group)
