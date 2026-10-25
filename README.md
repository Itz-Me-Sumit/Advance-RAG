# Advance RAG

A practical, stage-by-stage guide to building production-grade Retrieval-Augmented Generation systems. Every technique is implemented as a small, focused, runnable Python file, so you can learn one idea at a time and inspect exactly what each stage produces.

Part of the AI Engineer series: https://github.com/Itz-Me-Sumit/AI-Engineering

Prerequisite: the basics of LangChain, loaders, splitters, embeddings and retrievers are covered in https://github.com/Itz-Me-Sumit/GenAI

---

## Repository Structure

```
Advance RAG/
├── data/
│   ├── indexes/                # Saved vector / search indexes
│   ├── input/
│   │   ├── documents/          # Markdown and text documents
│   │   ├── images/             # Images used in multimodal demos
│   │   ├── pdfs/               # TechNova PDFs used by the parsing demo
│   │   ├── sample_data/        # Small sample files
│   │   ├── tables/             # Table data
│   │   ├── image_catalog.csv   # Image metadata catalog
│   │   ├── metadata_catalog.csv  # Document metadata catalog
│   │   └── technova_graph.csv  # TechNova entity/relationship data
│   └── output/                 # Generated outputs
├── src/
│   ├── 1_Document_Ingestion/   # Stage 1: getting clean, structured data in
│   ├── 2_Chunking_Strategies/  # Stage 2: splitting documents without losing context
│   └── 3_Indexing_Strategies/  # Stage 3: deciding what gets stored and searched
├── requirements.txt
├── .env                        # API keys (not committed)
└── README.md
```

More stage folders will be added under `src/` as the series grows.

---

## Getting Started

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file for API keys (Stages 1 to 3 need none, everything runs locally)
5. Add TechNova PDFs to `data/input/pdfs/` and documents to `data/input/documents/`
6. Run any file directly, for example: `python src/3_Indexing_Strategies/raptor.py`

Every script has a built-in fallback sample, so it runs even when the input folders are empty.

---

## Dataset

All demos use a fictional company, TechNova, and its product NovaFlow (a workflow automation platform) as the running example: PDFs, documents, tables, images and a small knowledge graph. One consistent dataset makes it easy to compare how each technique changes the result.

---

## Stage 1. Document Ingestion  (`src/1_Document_Ingestion`)

Basic RAG flattens a document into one stream of text. That loses page boundaries, tables, headings and reading order, and retrieval quality suffers from the very first step. This stage focuses on getting data in with structure, provenance and clean text intact, before any chunking or embedding happens.

### advance_pdf_parsing.py

Reads every PDF in `data/input/pdfs/` with PyMuPDF, block by block, instead of as one flat string.

- `parse_pdf`: iterates pages and text blocks (sorted in reading order) and returns one record per block with `source`, `page`, `block`, `kind` and `text`
- `classify_line`: simple heuristics label a line as `heading` (short, all caps or ending with a colon), `table-row` (wide column gaps or pipe characters) or `paragraph`
- Classification runs on the raw text first and whitespace is normalized afterwards, because normalizing first would erase the column gaps the table heuristic depends on
- Page number is kept on every record, so chunks can later cite their source page

Needs `pip install pymupdf`. Scanned PDFs additionally need OCR (for example Tesseract).

### structural_document_parsing.py

Splits a Markdown document into sections using its heading hierarchy instead of fixed-size pieces.

- `parse_sections`: walks the document line by line and tracks the current heading stack
- Each section is emitted as a record with a `path` (for example `NovaFlow > Deployment > Requirements`) and its body `text`
- Reads `data/input/documents/products_and_pricing.md`, with an inline TechNova sample as fallback
- The heading path is useful metadata for retrieval: a chunk always knows where in the document it came from

### document_cleaning.py

Removes common extraction noise before text reaches chunking and embedding.

- Drops repeated header/footer lines such as `Confidential - TechNova` and `Page 2 of 4`
- Rejoins words broken across lines by hyphenation (`Nova-\nFlow` becomes `NovaFlow`)
- Collapses repeated spaces, tabs and blank lines
- Prints character counts before and after, so the effect of cleaning is easy to see

### metadata_enrichment.py

Builds useful metadata for each document so retrieval can filter and cite sources.

- `enrich`: returns `source`, `title` (derived from the file name), `format`, `modified_date`, `character_count`, `topics` and `organization`
- `infer_topics`: keyword-based topic tagging (security, deployment, cloud, search, api, pricing)
- Reads the first `.md` or `.txt` file from `data/input/documents/`, with an inline sample as fallback
- Metadata like this enables filtered search (for example only security documents) and source citation in answers

### Key takeaways

- PDFs store positioned drawing commands, not paragraphs, so extraction needs care
- Keep page-level provenance and heading paths for citations
- Clean the text before chunking, noise creates bad embeddings
- Metadata is what makes filtered retrieval possible later

---

## Stage 2. Chunking Strategies  (`src/2_Chunking_Strategies`)

Fixed-size chunking is the usual starting point, and it is where many RAG problems begin. A chunk can cut a section in half, lose the heading it belongs to, or be too small to answer a question on its own. This stage compares five strategies. Each one fixes a different failure, and none of them is the best choice for every document.

All demos are dependency-free: retrieval is simulated with simple word-overlap scoring, so the effect of each chunking strategy is visible without embeddings or an API key.

### structural_chunking.py

Chunks Markdown by its heading structure, then enforces a size limit.

- Tracks the heading path while reading (for example `NovaFlow > Deployment`) and groups paragraphs under their section
- Splits oversized paragraphs and packs paragraphs into chunks of at most `max_words`
- Every chunk carries its section breadcrumb as metadata
- Best for: documentation, manuals and policies with clear headings

### sentence_window_chunking.py

Indexes single sentences but returns the sentence together with its neighbors.

- `build_window`: creates one record per sentence with a `focus` sentence and a `window` of surrounding sentences (`radius` controls how many on each side)
- Search matches the precise sentence, the LLM receives the wider window
- Best for: dense text where the answer sentence depends on the sentences around it

### parent_child_chunking.py

Search on small pieces, answer with large ones.

- `build_hierarchy`: paragraphs become parents (with a stable hash ID), sentences become children linked to their parent
- A query is matched against child sentences, then expanded to the full parent paragraph
- Small children give precise matching, large parents give enough context for generation
- Best for: long documents where precision and context are both needed

### semantic_chunking.py

Splits where the topic changes instead of at a fixed size.

- Each sentence becomes a word-count vector and neighboring sentences are compared with cosine similarity
- If similarity is above the threshold the sentence joins the current chunk, otherwise a new chunk starts
- In production, word counts would be replaced with embeddings for the same idea
- Best for: text without headings, where topics shift inside long passages

### contextual_chunking.py

Adds document and section context to each chunk before it is embedded.

- `contextualize`: prefixes every line with `Document: <title>, Section: <section>`
- The original text is kept for display, and the context-rich `embedding_text` is used for search
- The demo shows a query matching better with context than without
- Best for: short chunks that lose meaning once separated from their section

### Key takeaways

- Chunking decides what the retriever can find, so it deserves as much care as the model
- Small chunks are better for matching, large chunks are better for answering. Parent-child and sentence-window get both
- Context attached to a chunk (headings, titles) often matters more than the chunk size itself
- There is no single best strategy: the right choice depends on the document type and the questions asked

---

## Stage 3. Indexing Strategies  (`src/3_Indexing_Strategies`)

Basic RAG stores one flat collection of raw chunks, with one vector per chunk. That creates three problems. Broad questions retrieve small details without the overview that frames them. Users ask questions, while documents are written as statements, so the wording rarely matches. And a chunk on its own often loses the context it needs. This stage changes what gets stored and searched, not how the text is split.

All demos run locally with simple keyword overlap or TF-IDF, no API key needed. In production, the same ideas use dense embeddings, and an LLM generates the summaries and questions. The hierarchy and lineage logic stays deterministic.

### contextual_embeddings.py

Compares the same passages embedded two ways: raw, and with document and section context added.

- `tfidf_vectors`: builds a TF-IDF vector for every text from scratch (term frequency times inverse document frequency)
- `similarity`: cosine similarity between two sparse vectors
- Each line is indexed twice: as it is, and prefixed with `TechNova Document <title>; section <section>`
- The query is scored against both versions, so the effect of the added context is visible in the score
- Best for: passages like "It runs every fifteen minutes", where the key subject lives only in the heading

### hierarchical_indexing.py

Builds document, section and paragraph levels, then searches from coarse to fine.

- `build_tree`: reads Markdown headings and creates a tree with stable IDs (hash of title and position) and a `parent_id` on every node
- Each section gets a summary, and the document gets a summary listing its sections
- Search first selects the best section summary, then looks for the best paragraph only inside that section
- Prints the full lineage (`document -> section -> detail`) and a citation-style reference such as `Document > Section [id]`
- Best for: long manuals and naturally nested knowledge

### hypothetical_questions_indexing.py

Indexes questions that each passage could answer, instead of the passage itself.

- `questions_for`: generates likely questions for a passage (rule-based in this demo, LLM-generated in production)
- Each question is stored with the `doc_id` of its source passage
- A user query is matched against the generated questions, and the original passage is returned through `doc_id`
- A question matches another question better than a statement does
- Best for: FAQ-style and factual content where users ask direct questions

### multi_vector_indexing.py

Stores several representations of one document and searches across all of them.

- `build_index`: creates five representations per document: title, summary (first sentence), top keywords, a likely question and the full body
- `rank_documents`: scores every representation, then keeps only the best one per source document
- Prints how many representation hits were reduced to unique documents, and which representation matched
- Best for: documents that users find in different ways, by name, by topic or by question

### raptor.py

A simplified version of RAPTOR: a tree of summaries built bottom-up.

- `build_tree`: starts with the original passages as leaves, pairs each node with its most similar partner, and writes a summary parent for every pair. This repeats until one root remains
- `summarize`: deterministic summary with product names and top keywords (an LLM would write this in production)
- Search finds the best node at every level, picks the strongest summary, then `descend` follows the best-matching children down to a leaf
- Detailed questions are answered from leaves, broad questions from higher-level summaries
- Best for: long corpora where questions range from specific facts to overall themes

### Key takeaways

- What you store decides what you can find. Indexing is a design choice, not a default
- Summaries and generated questions help match how people ask, not how documents are written
- Keep lineage (parent IDs) so every answer can cite its exact source
- Deduplicate when one document has several representations
- Again, there is no single best strategy: pick the index based on the document structure and the type of questions

---

## What Comes Next

More stages (retrieval, re-ranking, evaluation and beyond) will be added to `src/` step by step.

- Agentic AI: LangGraph, MCP, multi-agent systems  https://github.com/Itz-Me-Sumit/Agentic-AI

---

## Author

Sumit
- GitHub: https://github.com/Itz-Me-Sumit
- LinkedIn: https://www.linkedin.com/in/sumit-kumar-809687360/

If this repository helps you, consider giving it a star.