# Phase 1: Baseline Data Pipeline & RAG Evaluation Report

## 1. Data Ingestion Summary
- **Source**: Crossref REST API
- **Query Filter**: `agentic retrieval augmented generation large language model`
- **Total Records Ingested**: 24
- **Status**: Raw API responses saved to `data/raw/` and parsed records cleaned into `data/clean/`.

## 2. Data Observability & Quality Signals
- **Data Quality Check**: `PASSED`
- **Freshness Monitoring**: `FRESH` (Stale rows: 0)
- **Latest Published Date**: 2026-08-05
- **Oldest Published Date**: 2026-02-12

### Detailed Quality Checks
| Check Name | Status | Actual Value | Expected |
| --- | --- | --- | --- |
| min_row_count | PASSED | 24 | > 0 |
| paper_id_not_null | PASSED | 0 | 0 |
| paper_id_unique | PASSED | 0 | 0 |
| title_not_null | PASSED | 0 | 0 |
| summary_sufficient_length | PASSED | 0 | 0 short or null summaries |
| freshness_threshold | PASSED | 0 | 0 rows older than 180 days |

## 3. RAG Retrieval & Answer Quality Metrics
- **Total Evaluated Samples**: 40
- **Retrieval Hit Rate**: `100.00%`
- **Mean Token F1 Score**: `1.0000`
- **Judge Accuracy**: `100.00%`
- **Mean Judge Score (1-5)**: `5.00 / 5.0`

## 4. Summary & Verification
Baseline pipeline executed successfully. The clean corpus indexed in ChromaDB provides accurate context for the RAG agent and establishes the benchmark metric for comparison.
