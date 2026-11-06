from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
FACTS = [
    "TechNova workflow automation is provided by NovaFlow.",
    "Failed NovaFlow runs can be replayed for fourteen days.",
    "NovaSecure manages NovaFlow access reviews.",
    "NovaSecure security logs are retained for 400 days.",
]

def terms(text: str) -> set[str]:
    """Extract normalized search terms from text.
    
    Args:
        text: The text to inspect or compare.
    Returns: A set of normalized terms.
    """    
    return set(re.findall(r"[a-z]{4,}", text.lower()))


def retrieve(query:str, excluded: set[int] | None = None) -> tuple[int, str]:
    """Find the passage with the greatest term overlap.
    
    Args:
        query: The user question or search text.
        excluded: Document indexes to skip.
    Returns: The best matching passage, with its index when applicable.
    """

    # Use an empty set when no docs need to be excluded.
    excluded = excluded or set()    

    # keep only documents that are not in the excluded set.
    candidates = [
        (i, text)
        for i, text in enumerate(FACTS)
        if i not in excluded
    ]

    # Return the document with the highest number of overlapping query terms.
    return max(
        candidates,
        key = lambda item: len(terms(query) & terms(item[1]))
    )

def extract_service(text: str) -> str:
    """Extract a supported service name from evidence text.
    
    Args:
        text: The text to inspect or compare.
    Returns: The supported service name found in the text.
    """    

    # Look for one of the supported service names as complete word.
    match = re.search(r"\b(NovaFlow|NovaSecure|NovaDesk)\b", text)


    if not match:
        raise ValueError("No supported intermidiate service found in the first-hop evidence")
    
    # Return the service name captured by the regular expression
    return match.group(1)


def main() -> None:
    query = "How long can failed runs from TechNova's workflow product be replayed?"
    first_query = "Which product provides TechNova workflow automation?"

    first_id, first = retrieve(first_query)
    service = extract_service(first)

    second_query = f"How long can failed {service} runs be replayed?"
    _, second = retrieve(second_query, {first_id})

    print(f"[original] -> {query}\n")
    print(f"[hop1 query] -> {first_query}")
    print(f"[hop1 evidence] -> {first}\n")
    print(f"[bridge entity] -> {service}\n")
    print(f"[hop2 query] -> {second_query}")
    print(f"[hop2 evidence] -> {second}\n")

if __name__=="__main__"    :
    main()