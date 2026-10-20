# Advance RAG

A practical, stage-by-stage guide to building production-grade Retrieval-Augmented Generation systems. Every technique is implemented as a small, focused, runnable Python file, so you can learn one idea at a time and inspect exactly what each stage produces.

Part of the AI Engineer series: https://github.com/Itz-Me-Sumit/AI-Engineer

Prerequisite: the basics of LangChain, loaders, splitters, embeddings and retrievers are covered in https://github.com/Itz-Me-Sumit/GenAI

---

## Repository Structure

```
Advance RAG/
├── data/
│   ├── indexes/                # Saved vector / search indexes
│   ├── input/
│   │   ├── documents/          # Source documents
│   │   ├── images/             # Images used in multimodal demos
│   │   ├── pdfs/               # TechNova PDFs used by the parsing demos
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
4. Create a `.env` file and add your API keys (only needed by demos that call an LLM)
5. Add the TechNova PDFs to `data/input/pdfs/`
6. Run any file directly, for example: `python src/1_Document_Ingestion/advance_pdf_parsing.py`

---

## Dataset

All demos use a fictional company, TechNova, as the running example: PDFs, documents, tables, images and a small knowledge graph. Using one consistent dataset makes it easy to compare how each technique changes the result.

---

## Stage 1. Document Ingestion  (`src/1_Document_Ingestion`)

Basic RAG usually flattens a document into one stream of text. That loses page boundaries, tables, headings and reading order, and retrieval quality suffers from the very first step. This stage focuses on getting data in with structure and provenance intact.

- `advance_pdf_parsing.py`: Reads every TechNova PDF with PyMuPDF block by block. Keeps page number and block number for each piece of text, and uses simple heuristics to label each block as a heading, table-row or paragraph. The output records can be chunked later without losing page metadata. Runs locally, no API key needed.
- `structural_document_parsing.py`: Parses documents using their structure (headings, sections, hierarchy) instead of treating them as flat text.
- `document_cleaning.py`: Cleans extracted text (noise, whitespace, boilerplate) before it reaches chunking and embedding.
- `metadata_enrichment.py`: Attaches useful metadata to documents and chunks, supporting filtered retrieval and source citation.

Key takeaways:
- PDFs store positioned drawing commands, not paragraphs, so extraction needs care
- Always keep page-level provenance for citations
- Layout classification must see the raw spacing, so normalize text only after classifying
- Scanned PDFs additionally need OCR (for example Tesseract)

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