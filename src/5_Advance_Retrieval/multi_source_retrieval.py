from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DOC_DIR = ROOT / "data" / "input" / "documents"
SOURCES = {
    "product_docs": ["Failed NovaFlow runs can be replayed for fourteen days."],
    "support_notes": ["NovaFlow PDF failures may indicate a scanned document requiring OCR."],
    "service_status": ["NovaFlow workflow service: operational; updated 2026-09-11."],
}

def terms(text: str) -> set[str]:
    """Extract normalized search terms from text.
    
    Args:
        text: The text to inspect or compare.
    Returns: A set of normalized terms.
    """
    normalized = []    
    for word in re.findall(r"[a-z]{4,}", text.lower()):
        # Example: "running" -> "runn", "failed" -> "fail", "failures" -> "fail"        
        normalized.append(re.sub(r"(ing|ures|ure|ed|s)$", "", word))
    return set(normalized)


def search_source(name: str, query: str, rows: list[str]) -> list[dict]:
    """Search one named source for matching rows.
    
    Args: name: The source name attached to each result.; query: The user question or search text.
        rows: The source passages to search.
    Returns: Matching rows with source labels and normalized scores.
    """    

    query_terms = terms(query)

    scored = [(len(query_terms & terms(text)), text) for text in rows]

    # Normalize by the number of query terms so scores are comparable across sources.
    # Example: 3 matching terms out of 4 -> score = 0.75
    return [{"source": name, "text": text, "score": score / max(len(query_terms), 1)}
            for score, text in scored if score]

def main() -> None:
    query = "Why is a NovaFlow PDF failing, and is the workflow service operational?"
    merged = []

    for source, rows in SOURCES.items():
        hits = search_source(source, query, rows)
        merged.extend(hits)
        print(f"[source] {source}: {len(hits)} matching records.")

    print("[merged ranking]")
    for hit in sorted(merged, key= lambda item: item["score"], reverse=True):
        print(f"    {hit['score']:.2f} [{hit['source']}] ->> {hit['text']}")

if __name__=="__main__":
    main()