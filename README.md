# IKEA Assembly Instruction Processing

A **Retrieval-Augmented Generation (RAG)** pipeline that scrapes IKEA product pages, converts PDF assembly manuals into structured data using Docling, and indexes the result into **LanceDB** for semantic search and Q&A.

---

> [!NOTE]
> **Disclaimer:** The PDF assembly instruction files used in this project are publicly available documents provided by IKEA on their official website ([ikea.com](https://www.ikea.com)). They are used here solely for research and educational purposes. All intellectual property rights remain with IKEA. This project is not affiliated with or endorsed by IKEA.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Directory](#data-directory)
- [Development](#development)

---

## Overview

The pipeline performs the following steps end-to-end:

1. **Web Scraping** – Scrapes IKEA product category pages with Playwright to collect product links and PDF manual URLs.
2. **PDF Processing** – Downloads manuals and converts them to Markdown using Docling (with OCR, table extraction, and optional vision-model image description).
3. **Chunking** – Splits Markdown documents into semantic chunks (by heading hierarchy and page breaks).
4. **Data Transformation** – Transforms raw chunks into structured assembly/guidance records via configurable extraction strategies.
5. **Embedding & Ingestion** – Embeds chunks with `ibm-granite/granite-embedding-97m-multilingual-r2` and writes them to a LanceDB vector store via Haystack pipelines.

---

## Project Structure

```
IKEA_Assembly_Instruction_Processing/
│
├── src/                                  # Core source package
│   ├── components/                       # Haystack components (pipeline nodes)
│   │   ├── chunk_data_process.py         # Transforms raw Markdown chunks into structured rows
│   │   ├── chunk_file_generator.py       # Splits Markdown by page/header patterns
│   │   ├── data_chunk_to_document_conversion.py  # Converts dicts to Haystack Documents
│   │   ├── fixed_lancedb_document_store.py       # Patched LanceDB document store
│   │   ├── lancedb_data_ingestion_process.py     # Embedding + LanceDB write pipeline node
│   │   ├── lancedb_data_processing.py            # Schema prep & table definitions
│   │   ├── parse_product_category_links.py       # Scrapes category listing pages
│   │   ├── parse_product_details_and_manual_download.py  # Downloads PDFs & metadata
│   │   ├── parse_product_links.py        # Extracts individual product URLs
│   │   ├── picture_description_vl.py     # Vision-model image captioning (Granite/Qwen)
│   │   ├── system_prompt_generation.py   # Builds system prompts for LLM calls
│   │   └── user_prompt_generation.py     # Builds user prompts for LLM calls
│   │
│   ├── pipelines/                        # Haystack pipeline factories
│   │   ├── web_scrapping_pipeline.py     # End-to-end web scraping pipeline
│   │   ├── document_chunk_generation.py  # PDF → Markdown → chunk pipeline
│   │   ├── picture_description_pipeline.py  # Image captioning pipeline
│   │   ├── chunk_data_processing.py      # Chunk transformation pipeline
│   │   ├── lancedb_processing_pipeline.py   # LanceDB schema processing pipeline
│   │   ├── lancedb_data_ingestion.py     # Embedding + ingestion pipeline
│   │   └── system_user_prompts_generation.py  # Prompt generation pipeline
│   │
│   ├── tools/
│      └── transformation_functions.py   # Field extraction & data transformation helpers
│   
│
├── scripts/                              # Entry-point scripts
│   ├── main_pipeline.py                  # Full end-to-end async pipeline runner
│
├── config/                               # Configuration layer
│   ├── config_settings.py                # Pydantic Settings models (all tuneable knobs)
│   └── log_config.py                     # Logging setup
│
├── data/                                 # Runtime data (git-ignored large files)
│   ├── pdf_files/                        # Source IKEA PDF manuals
│   ├── markdown_files/                   # Docling-converted Markdown output
│   ├── LanceDB_data/                     # LanceDB on-disk database
│   ├── lanceDB_metadata/                 # Table definitions & column mappings (JSON)
│   ├── graph_vector_metadata/            # FalkorDB node DDL & mapping files
│   ├── prompts/                          # System & user prompt templates
│   ├── product_details.csv               # Scraped product metadata
│   └── product_links.csv                 # Scraped product URLs
│
├── logs/                                 # Application log files
├── pyproject.toml                        # Project metadata & dependencies
├── requirement.txt                       # Full pinned dependency list
```

---

## Architecture

```
IKEA Website
     │
     ▼
Web Scraping Pipeline  (Playwright + parse_product_* components)
     │  product links, PDF URLs, metadata
     ▼
PDF Download & Docling Conversion  (docling_processing.py)
     │  Markdown files
     ▼
Chunking Pipeline  (chunk_file_generator → chunk_data_process)
     │  structured assembly/guidance chunk rows
     ▼
LanceDB Processing Pipeline  (lancedb_data_processing)
     │  schema-validated table data
     ▼
Embedding & Ingestion Pipeline  (lancedb_data_ingestion_process)
     │  granite-embedding → LanceDB IVF_PQ index
     ▼
LanceDB Vector Store  (on-disk, query-ready for RAG)
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.11 |
| Ollama (optional, for vision) | latest |
| FalkorDB (optional, graph store) | latest |

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd IKEA_Assembly_Instruction_Processing

# 2. Create and activate a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Install the project and its dependencies
pip install -e .
pip install -r requirement.txt

# 4. Install Playwright browsers (needed for web scraping)
playwright install chromium
```

---

## Configuration

All settings are controlled by **Pydantic Settings** models in `config/config_settings.py`. Values can be overridden via environment variables or a `.env` file in the project root.

### Key Configuration Sections

| Section | Class | Key Settings |
|---|---|---|
| LanceDB | `LanceDBConfig` | `uri`, `tablename`, `index_type` (`IVF_PQ`/`IVF_HNSW_SQ`), `embedding_model` |
| Chunking | `ChunkSettingConfig` | `chunk_size` (default 512), `chunk_overlap` (default 100) |
| PDF Source | `DatasourceConfig` | `pfdfile_path`, `markdown_files_path` |
| Docling | `DoclingConfig` | `do_ocr`, `do_table_structure`, `do_picture_description`, `vision_model_name` |
| IKEA Scraper | `IKEAConfig` | `country` (default `nl`), `language` (default `en`) |
| Logging | `ConfigSettings` | `log_level`, `log_file_path` |

### `.env` example

```dotenv
# Override any ConfigSettings field
LOG_LEVEL=DEBUG
ENVIRONMENT=DEV
```

---

## Usage

### Run the Full Pipeline

```bash
python -m scripts.main_pipeline
```

This runs the complete async pipeline:
1. Scrapes IKEA product pages
2. Downloads and converts PDFs to Markdown
3. Chunks and transforms assembly data
4. Embeds and ingests into LanceDB

### Run Individual Pipelines

Individual pipeline factories in `src/pipelines/` can be imported and composed independently:

```python
from config.config_settings import ConfigSettings
from src.pipelines.lancedb_data_ingestion import create_lancedb_ingestion_pipeline

settings = ConfigSettings()
pipeline = create_lancedb_ingestion_pipeline(settings)
pipeline.run({'LanceDBDataIngestionProcess': {'input': product, 'table_data': data}})
```

---

## Data Directory

| Folder | Description |
|---|---|
| `data/pdf_files/` | Raw IKEA PDF manuals downloaded by the scraper |
| `data/markdown_files/` | Markdown conversions produced by Docling |
| `data/LanceDB_data/` | LanceDB on-disk vector store (IVF_PQ indexed) |
| `data/lanceDB_metadata/` | `table_definition_lancedb.json` and column mapping JSONs |
| `data/prompts/` | System and user prompt template files |

---

## Development

```bash
# Run tests
python -m pytest tests/

# Check static types
pyright

# View logs
tail -f logs/DEV_IKEA_Assembly_Instruction_Processing.log
```

### Embedding Model

The pipeline uses `ibm-granite/granite-embedding-97m-multilingual-r2` (saved locally to `embedding_model/`). The first run downloads and caches the model automatically.

### Vision Model (Optional)

Image description uses Ollama with `qwen3.5:2b` (configurable via `docling_config.vision_model_name`). Ensure Ollama is running locally before enabling `do_picture_description = True`.
