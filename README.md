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
│   └── 1_Document_Ingestion/   # Stage 1: getting clean, structured data in
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
4. Create a `.env` file for API keys (Stage 1 needs none, everything runs locally)
5. Add TechNova PDFs to `data/input/pdfs/` and documents to `data/input/documents/`
6. Run any file directly, for example: `python src/1_Document_Ingestion/advance_pdf_parsing.py`

Every Stage 1 script has a built-in fallback sample, so it runs even when the input folders are empty.

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

## What Comes Next

More stages (chunking, retrieval, re-ranking, evaluation and beyond) will be added to `src/` step by step.

- Agentic AI: LangGraph, MCP, multi-agent systems  https://github.com/Itz-Me-Sumit/Agentic-AI

---

## Author

Sumit
- GitHub: https://github.com/Itz-Me-Sumit
- LinkedIn: https://www.linkedin.com/in/sumit-kumar-809687360/

If this repository helps you, consider giving it a star.