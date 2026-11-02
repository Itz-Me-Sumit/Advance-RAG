# Hybrid = combine retrieval scores.
# Ensemble = combine rankings from different retrievers/signals.
    
# Ensemble: consider optional, because RRF/fusion was already covered in your Query Transformation section. 

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
DOC_DIR = ROOT / "data" / "input" / "documents"
DOCS = [
    {"text": "Failed NovaFlow runs can be replayed for fourteen days.", "authority": 3},
    {"text": "Unsuccessful NovaFlow executions remain rerunnable for two weeks.", "authority": 2},
    {"text": "A community note suggests rebuilding failed workflows.", "authority": 1},
]
SYNONYMS = {"replay": {"rerunnable", "rerun"}, "failed": {"failures", "unsuccessful"}}


def terms(text: str) -> set[str]:
    """Extract normalized search terms from text.
    
    Args:
        text: The text to inspect or compare.
    Returns: A set of normalized terms.
    """
    return set(re.findall(r"[a-z]{4,}", text.lower()))


def lexical_rank(query: str) -> list[int]:
    """Rank documents using exact term overlap.
    
    Args:
        query: The user question or search text.
    Returns: Document indexes ordered by lexical relevance.
    """
    # Compare the query terms with the terms in each document.
    # The intersection (&) gives us the terms appearing in both.
    # Example:
    # query  = {"novaflow", "failed", "run"}
    # doc    = {"novaflow", "failed", "workflow"}
    # overlap = {"novaflow", "failed"} -> score = 2
    return sorted(
        range(len(DOCS)),
        key=lambda i: len(terms(query) & terms(DOCS[i]["text"])),
        reverse=True,
    )


def semantic_rank(query: str) -> list[int]:
    """Rank documents after expanding query terms with synonyms.
    
    Args:
        query: The user question or search text.
    Returns: Document indexes ordered by synonym-aware relevance.
    """
    # Start with the normal terms from the query.
    expanded = terms(query)

    # Add known synonyms/aliases for every query term.
    # Example:
    # query term = "failed"
    # SYNONYMS["failed"] = {"unsuccessful", "error"}
    # expanded now contains the original term plus its synonyms.
    #
    # list(expanded) creates a snapshot so we can safely add new terms
    # to the set while iterating.
    for term in list(expanded):
        expanded |= SYNONYMS.get(term, set())

    # Rank documents by how many expanded query terms they contain.
    # A document matching either the original term or a known synonym
    # can therefore receive a higher relevance score.
    return sorted(
        range(len(DOCS)),
        key=lambda i: len(expanded & terms(DOCS[i]["text"])),
        reverse=True,
    )


def main() -> None:
    """Run the tutorial demonstration."""

    # Define the user's search query.
    query = "How long can TechNova replay a failed NovaFlow run?"

    # Create three different rankings of the same documents.
    #
    # Each tuple contains:
    # (weight assigned to this retriever, document ranking)
    #
    # Higher weight means that retriever has a stronger influence
    # on the final fused ranking.
    rankings = [
        (0.45, lexical_rank(query)),  # 45% weight: exact term matching
        (0.40, semantic_rank(query)), # 40% weight: synonym-aware matching

        # 15% weight: rank documents by their authority score.
        # Documents with higher authority appear earlier in this ranking.
        (0.15, sorted(
            range(len(DOCS)),
            key=lambda i: DOCS[i]["authority"],
            reverse=True,
        )),
    ]

    # Start every document with a fusion score of 0.
    # Example: {0: 0.0, 1: 0.0, 2: 0.0}
    fused = {index: 0.0 for index in range(len(DOCS))}

    # Process each retriever's ranking separately.
    for weight, ranking in rankings:

        # Go through the documents in their ranked order.
        # rank starts at 1, so the first document has rank 1,
        # the second has rank 2, and so on.
        for rank, doc_id in enumerate(ranking, 1):

            # Add this retriever's contribution to the document's
            # overall fusion score.
            #
            # Formula:
            # contribution = retriever_weight / (60 + rank)
            #
            # A document ranked higher receives a larger contribution.
            # Example with weight=0.45:
            # rank 1 -> 0.45 / 61
            # rank 2 -> 0.45 / 62
            #
            # The contributions from all three rankings are accumulated.
            fused[doc_id] += weight / (60 + rank)

    print(f"[query] {query}")
    for doc_id in sorted(fused, key=fused.get, reverse=True):
        print(f"[ensemble] {fused[doc_id]:.4f} | {DOCS[doc_id]['text']}")
    print(f"[data hint] Real documents may live under {DOC_DIR}")


if __name__ == "__main__":
    main()