"""
Maximal Marginal Relevance (MMR) retrieval demonstration.

MMR balances two goals:
1. Retrieve documents relevant to the query.
2. Avoid selecting documents that repeat information already selected.

The minimum relevance threshold prevents MMR from selecting completely
irrelevant documents simply because the requested result count has not
yet been reached.
"""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DOCS = [
    "Failed NovaFlow runs can be replayed for fourteen days.",
    "NovaFlow unsuccessful executions remain rerunnable for two weeks.",
    "NovaFlow support can help diagnose failed PDF ingestion problems.",
    "NovaFlow support can provide the failed job identifier for investigation.",
]
DOC_DIR = ROOT / "data" / "input" / "documents"


def terms(text: str) -> set[str]:
    """Extract normalized search terms from text.

    Args:
        text: The text to inspect.
    Returns:
        A set of lowercase words containing at least four letters.
    """
    return set(re.findall(r"[a-z]{4,}", text.lower()))


def similarity(left: str, right: str) -> float:
    """Calculate Jaccard similarity between two texts.

    Args:
        left: The first text to compare.
        right: The second text to compare.
    Returns:
        A similarity value between zero and one.
    """
    # Convert both texts into sets of normalized terms.
    left_terms = terms(left)
    right_terms = terms(right)

    # Jaccard similarity = shared terms / total unique terms.
    # Example: {a, b} and {b, c} -> 1 / 3 = 0.333
    return (
        len(left_terms & right_terms) / len(left_terms | right_terms)
        if left_terms | right_terms
        else 0.0
    )


def mmr(
    query: str,
    documents: list[str],
    count: int = 3,
    weight: float = 0.65,
    min_relevance: float = 0.05,
) -> list[str]:
    """Select relevant and diverse passages using MMR.

    Args:
        query: The user question or search text.
        documents: Candidate passages to retrieve.
        count: Maximum number of results to return.
        weight: Balance between relevance and diversity.
        min_relevance: Minimum relevance required for a document to qualify.
    Returns:
        Selected passages in MMR ranking order.
    """
    # Keep selected documents separate from the candidates still available.
    selected = []
    remaining = documents.copy()

    while remaining and len(selected) < count:
        scored = []

        for document in remaining:
            # Measure how relevant this document is to the query.
            relevance = similarity(query, document)

            # Skip documents that are not relevant enough.
            if relevance < min_relevance:
                continue

            # Measure how much this document repeats already-selected information.
            # Higher redundancy means more overlap with an existing result.
            redundancy = max(
                (similarity(document, chosen) for chosen in selected),
                default=0.0,
            )

            # MMR rewards relevance and penalizes redundancy.
            # Example: high relevance + low redundancy -> high MMR score.
            mmr_score = (
                weight * relevance
                - (1 - weight) * redundancy
            )

            scored.append(
                (mmr_score, relevance, redundancy, document)
            )

        # Stop if no remaining document meets the relevance threshold.
        if not scored:
            break

        # Select the document with the highest MMR score.
        score, relevance, redundancy, winner = max(
            scored,
            key=lambda item: item[0],
        )

        print(
            f"[select] mmr={score:.3f} "
            f"relevance={relevance:.3f} "
            f"redundancy={redundancy:.3f} | {winner}"
        )

        selected.append(winner)
        remaining.remove(winner)

    return selected


def main() -> None:
    """Run the tutorial demonstration."""

    query = "How long can a failed NovaFlow run be replayed and what support helps?"

    print(f"[query] {query}")

    # Ask MMR for up to three results while requiring every result
    # to have at least some relevance to the query.
    results = mmr(
        query,
        DOCS,
        count=3,
        weight=0.65,
        min_relevance=0.05,
    )

    print(f"[result] selected {len(results)} relevant and diverse passages")
    print(f"[data hint] Real local documents: {DOC_DIR}")


if __name__ == "__main__":
    main()