# Data Pipeline Observability: Baseline vs Corrupted vs Repaired Report

## 1. Executive Summary
This report analyzes the impact of intentional data quality degradation (corruption) on RAG retrieval accuracy and LLM answer generation, as well as the recovery achieved after re-ingesting clean raw data.

## 2. Evaluation Metrics Comparison

| Metric | Baseline | Corrupted | Repaired | Impact (Corrupted vs Baseline) | Recovery (Repaired vs Corrupted) |
| --- | --- | --- | --- | --- | --- |
| **Retrieval Hit Rate** | 100.0% | 80.0% | 100.0% | -20.0% | +20.0% |
| **Mean Token F1** | 1.0000 | 0.8030 | 1.0000 | -0.1970 | +0.1970 |
| **Judge Accuracy** | 100.0% | 80.0% | 100.0% | -20.0% | +20.0% |
| **Mean Judge Score** | 5.00 | 4.20 | 5.00 | -0.80 | +0.80 |

## 3. Data Observability & Quality Comparison

| State | Quality Checks Status | Freshness Status | Stale Rows | Total Rows |
| --- | --- | --- | --- | --- |
| **Baseline** | PASSED | FRESH | 0 | 40 |
| **Corrupted** | FAILED | STALE | 1 | 23 |
| **Repaired** | PASSED | FRESH | 0 | 24 |

## 4. Key Takeaways
1. **Corruption Impact**: Injecting blank summaries, stale dates, text noise, and dropping records directly degraded vector retrieval hit rate and LLM generation quality.
2. **Observability Detection**: Data quality gates and freshness checks flagged data degradation issues before deployment.
3. **Pipeline Recovery**: Repairing the data pipeline from original raw artifacts restored RAG accuracy to baseline levels.
