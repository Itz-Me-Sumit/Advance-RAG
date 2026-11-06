from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
INDEXES = {
    "novaflow": ["Failed NovaFlow runs can be replayed for fourteen days.", "NovaFlow automates workflows."],
    "novasecure": ["NovaSecure manages access reviews.", "Security logs are retained for 400 days."],
    "support": ["Scanned PDFs require OCR before ingestion.", "Contact support with the failed job identifier."],
}


def terms(text: str) -> set[str]:
    """Extract normalized search terms from text.
    
    Args:
        text: The text to inspect or compare.
    Returns: A set of normalized terms.
    """
    # Extract lowercase words with at least 3 letters and remove a trailing "s".
    # Example: "NovaFlows failed runs" -> {"novaflow", "failed", "run"}    
    return {word.removesuffix("s") for word in re.findall(r"[a-z]{3,}", text.lower())}


def select_indexes(query: str) -> list[str]:
    """Choose which indexes should handle a query.
    
    Args:
        query: The user question or search text.
    Returns: Index names to search, without duplicates.
    """
    # Convert the query to lowercase so index matching is case-insensitive.
    lowered = query.lower()

    # Select product-specific indexes when their names appear in the query.
    selected = [name for name in ("novaflow", "novasecure") if name in lowered]

    if any(term in lowered for term in ("error", "fail", "help", "ocr", "pdf")):
        selected.append("support")

    # Remove duplicates; if nothing matched, search all available indexes.
    return list(dict.fromkeys(selected) or list(INDEXES))


def main() -> None:
    query = "Why did my Novaflow PDF fail?"

    selected, results = select_indexes(query), []

    for index_name in selected:
        for text in INDEXES[index_name]:
            score = len(terms(query) & terms(text))
            if score:
                results.append({"index": index_name, "text": text, "score": score})

    print(f"[route] -> {query} -> {selected}")

    for hit in sorted(results, key = lambda item: item["score"], reverse=True):
        print(f"[result] -> score={hit['score']} index={hit['index']} | {hit['text']}")

if __name__=="__main__":
    main()