from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RECORDS = [
    {"text": "NovaFlow production workflow checklist.", "product": "novaflow", "year": 2026, "region": "global", "status": "active"},
    {"text": "NovaFlow retired installation procedure.", "product": "novaflow", "year": 2023, "region": "global", "status": "retired"},
    {"text": "NovaSecure EU security-log retention policy.", "product": "novasecure", "year": 2026, "region": "eu", "status": "active"},
    {"text": "NovaSecure US access review guide.", "product": "novasecure", "year": 2026, "region": "us", "status": "active"},
]


def filter_records(records: list[dict], filters: dict) -> list[dict]:
    """Keep records that match all requested metadata filters.
    
    Args:
        records: The records available for filtering.
        filters: Required metadata field values.
    Returns: Records satisfying every supplied filter.
    """

    allowed = {"product", "year", "region", "status"}    

    # identify any filter fields that are not in the allowed list.
    unknown = set(filters) - allowed
    if unknown:
        raise ValueError(f"Unsupported metadata fields: {sorted(unknown)}")
    
    # Keep a record only when every requested field matches its expected value.
    # Example: {"region": "eu", "status": "active"} requires both to match.    
    return [
        record
        for record in records
        if all(
            record.get(field) == expected
            for field, expected in filters.items()
        )
    ]


def score(query: str, text: str) -> int:
    """Measure keyword overlap between a query and passage.
    
    Args:
        query: The user question or search text.
        text: The text to inspect or compare.
    Returns: The number of meaningful terms shared by both texts.
    """
    words = lambda value: set(re.findall(r"[a-z]{4,}", value.lower()))
    return len(words(query) & words(text))


def main() -> None:

    query = "What is the current NovaSecure security-log policy?"
    filters = {"product": "novasecure", "region": "eu", "status": "active", "year": 2026}

    # First apply the hard metadata filters to reduce the candidate set
    candidates = filter_records(RECORDS, filters)

    ranked = sorted(
        candidates,
        key = lambda record: score(query, record["text"])
    )

    print(f"[query] -> {query}")
    print(f"[filters] -> {filters}")
    print(f"[candidate reduction] -> {len(RECORDS)} <<->> {len(candidates)}")
    print(f"[result] -> {ranked[0]['text'] if ranked else 'No results'}")

if __name__=="__main__":
    main()