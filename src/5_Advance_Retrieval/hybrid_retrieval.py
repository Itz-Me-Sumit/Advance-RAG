from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FALLBACK = [
    "Failed NovaFlow workflow runs can be replayed for fourteen days.",
    "Unsuccessful NovaFlow executions remain eligible for rerun for two weeks.",
    "NovaSecure security logs are retained for 400 days.",
    "NovaDesk exports remain available for seven days.",
]

SYNONYMS = {
    "replay": "rerun retry",
    "failed": "unsuccessful failure",
    "fourteen": "two weeks",
}

def documents() -> list[str]:
    return FALLBACK

def words(text: str) -> set[str]:
    """Extract lowercase search words from text.
    
    Args:
        text: The text to inspect or compare.
    Returns: The extracted lowercase words.
    """    
    return set(re.findall(r"[a-z0-9-]{2,}", text.lower()))


def bm25_scores(query: str, docs: list[str]) -> tuple[list[float], str]:
    """Calculate BM25 relevance scores for documents.
    
    Args:
        query: The user question or search text.
        docs: The documents to score.
    Returns: The document scores and the BM25 method name.
    """    

    # Example: "NovaFlow failed run" -> ["novaflow", "failed", "run"]
    tokenized = [re.findall(r"[a-z0-9-]{2,}", text.lower()) for text in docs]

    query_tokens = re.findall(r"[a-z0-9-]{2,}", query.lower())

    try:

        # BM25 compares the query terms with each document and gives higher scores to documents that are more relevant.
        from rank_bm25 import BM25Okapi

        return list(
            map(BM25Okapi(tokenized).get_scores(query_tokens))
        ), "rank_bm25.BM250kapi"
    
    except ImportError:
        # If rank_bm25 is not installed, calculate BM25 locally.
        # This keeps the script runnable without requiring the package.

        from collections import Counter
        from math import log

        # Calculate the avg number of token across all docs, this helps BM25 account for document of different lenghts
        average_length = sum(map(len, tokenized)) / max(len(tokenized), 1)

        # Ex: if "novaflow" appears in 3 documents, its document frequency is 3
        document_frequency = Counter(
            term for doc in tokenized for term in set(doc)
        )

        scores = []

        for doc in tokenized:
            
            # Ex: ["failed", "failed", "run"] -> {"failed": 2, "run": 1}
            frequency, score = Counter(doc), 0.0
        
            for term in query_tokens:
                
                # if the query term does not appear in this document, it contributed nothing to that document's BM25 score
                if not frequency[term]:
                    continue
                
                # IDF gives more importance to terms that appear in fewer documents and less importance to common terms.
                idf = log(
                    1
                    + (len(tokenized) - document_frequency[term] + 0.5)
                    / (document_frequency[term] + 0.5)
                )

                denominator = (
                    frequency[term]
                    + 1.5
                    * (
                        1
                        - 0.75
                        + 0.75 * len(doc) / average_length
                    )
                )

                score += idf * frequency[term] * 2.5 / denominator

            scores.append(score)

        # Return the scores and identity which BM25 implementation was using
        return scores, "local Robertson BM25"
    

def semantic_text(text: str) -> str:
    """Expand text with known synonyms for semantic matching.
    
    Args:
        text: The text to inspect or compare.
    Returns: The lowercased text with matching synonyms appended.
    """

    expanded = text.lower()    

    for term, aliases in SYNONYMS.items():
        
        # If the main term OR any of its aliases appears in the text, append both the main term and its aliases to the text.
        # Ex: "Novaflow unsuccessful" -> "novaflow failed error unsuccessful"
        if term in expanded or any(
            alias in expanded for alias in aliases.split()
        ):
            expanded += f" {term} {aliases}"

    return expanded


def vector_scores(query: str, docs: list[str]) -> list[float]:
    """Calculate TF-IDF cosine similarity scores.
    
    Args:
        query: The user question or search text.
        docs: The documents to score.
    Returns: One similarity score for each document.
    """    
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    # Create a TF-IDF vectorizer that considers both single words and
    # two-word phrases.
    # Example: "failed run" produces features such as "failed", "run",
    # and the bigram "failed run".
    matrix = TfidfVectorizer(ngram_range=(1,2)).fit_transform(
        # Put the query first, followed by all documents.
        # semantic_text() expands known synonyms before vectorization.        
        [semantic_text(query), *(semantic_text(doc) for doc in docs)]
    )

    # Compare the query vector (row 0) against every document vector.
    # Cosine similarity produces one score per document:
    # 1.0 = very similar direction, 0.0 = no overlap.
    return list(
        map(
            float,
            cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        )
    )

def main():

    query, docs = "How long can an unsuccessful Novaflow execution be rerun?", documents()

    # Calculate BM25 scores for every document.
    # BM25 captures keyword-based/lexical matching.
    # sparse_method tells us which BM25 implementation was used.
    sparse, sparse_method = bm25_scores(query, docs)

    # Calculate TF-IDF cosine similarity scores for every document.
    # This provides a second, different lexical matching signal.
    vectors = vector_scores(query, docs)

    # Find the highest BM25 score so we can normalize BM25 scores
    # to roughly the same 0-to-1 scale as the cosine similarity scores.
    # "or 1" prevents division by zero if every BM25 score is 0.
    max_sparse = max(sparse) or 1

    # Calculate a combined hybrid score for every document and sort
    # the documents from highest combined score to lowest.
    #
    # 0.55 * normalized BM25 = 55% weight for BM25
    # 0.45 * vector score    = 45% weight for TF-IDF similarity
    #
    # Each tuple contains:
    # (hybrid score, BM25 score, TF-IDF score, document text)
    ranked = sorted(
        (
            (
                0.55 * bm25 / max_sparse + 0.45 * vector,
                bm25,
                vector,
                text
            )
            for text, bm25, vector in zip(docs, sparse, vectors)
        ),
        reverse=True
    )

    print(f"[query] {query}")
    print(f"[sparse] {sparse_method}")
    
    print(f"[BM25 ranking] {sorted(range(len(docs)), key = lambda i : sparse[i], reverse=True)}")
    print(f"[vector ranking] {sorted(range(len(docs)), key = lambda i : vectors[i], reverse=True)}")

    for total, bm25, vector, text in ranked:
        print(f"[fusion] hybrid={total:.3f} bm25={bm25:.3f} vector={vector:.3f} | >> {text}")

if __name__=="__main__":
    main()