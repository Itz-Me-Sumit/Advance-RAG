from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DOC_DIR = ROOT / "data" / "input" / "documents"
RECORDS = [
    {"text": "NovaFlow Scale supports 100 active workflows.", "product": "novaflow", "year": 2026, "format": "md"},
    {"text": "NovaFlow legacy deployment notes.", "product": "novaflow", "year": 2024, "format": "pdf"},
    {"text": "NovaSecure access review administration guide.", "product": "novasecure", "year": 2026, "format": "md"},
]


def parse_query(query: str) -> tuple[str, dict]:
    """Separate search text from structured metadata filters.
    
    Args:
        query: The user question or search text.
    Returns: The remaining search text and extracted filters.
    """
    # Convert the query to lowercase and create an empty filter dictionary.
    lowered, filters = query.lower(), {}

    # Extract a supported product name as a metadata filter.
    for product in ("novaflow", "novasecure", "novadesk"):
        if product in lowered:
            filters["product"] = product

    # Extract a four-digit year and convert it from text to an integer.
    # Example: "Find 2026 documents" -> {"year": 2026}
    if year := re.search(r"\b20\d{2}\b", query):
        filters["year"] = int(year.group())

    # Extract the requested file format and normalize "markdown" to "md".
    if fmt := re.search(r"\b(pdf|markdown|md|txt)\b", lowered):
        filters["format"] = "md" if fmt.group() == "markdown" else fmt.group()

    # Remove metadata-related terms so the remaining text can be used
    # as the semantic search query.
    semantic = re.sub(
        r"\b(novaflow|novasecure|novadesk|20\d{2}|pdf|markdown|md|txt)\b",
        "",
        lowered,
    )

    return " ".join(semantic.split()), filters


def main() -> None:
    """Run the tutorial demonstration."""
    
    query = "Find 2026 Markdown NovaFlow active workflow limits"

    # Split the natural-language query into semantic search text and metadata filters.
    semantic, filters = parse_query(query)

    # Apply all extracted metadata filters before ranking the remaining candidates.
    candidates = [
        record
        for record in RECORDS
        if all(record.get(key) == value for key, value in filters.items())
    ]

    # Extract the meaningful terms from the semantic part of the query.
    terms = set(re.findall(r"[a-z]{4,}", semantic))

    # Rank the filtered records by the number of query terms they share.
    ranked = sorted(
        candidates,
        key=lambda r: len(
            terms & set(re.findall(r"[a-z]{4,}", r["text"].lower()))
        ),
        reverse=True,
    )
    
    print(f"[query] {query}")
    print(f"[parsed] semantic={semantic!r}, filters={filters}")
    print(f"[filter] {len(candidates)} of {len(RECORDS)} documents remain")
    print(f"[result] {ranked[0]['text'] if ranked else 'No matching document'}")
    print(f"[data hint] Add real documents under {DOC_DIR}")


if __name__ == "__main__":
    main()