from pathlib import Path

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def main() -> None:
    """Execute baseline Phase 1 end-to-end pipeline."""
    print("=== Step 1: Loading Settings & Ingesting Raw Data ===")
    settings = load_settings()
    records = fetch_source_records(settings)
    print(f"Fetched/Loaded {len(records)} raw records from {settings.source_api}.")

    print("=== Step 2: Cleaning Data & Building Clean DataFrame ===")
    run_dt = now_utc()
    df_clean = build_clean_dataframe(records, run_dt)
    write_csv(df_clean, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df_clean.to_dict(orient="records"))
    print(f"Cleaned dataset contains {len(df_clean)} records. Saved to {settings.paths.clean_csv}.")

    print("=== Step 3: Building Vector Store & Embedding Index ===")
    index = LocalEmbeddingIndex.build(
        df=df_clean,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(f"Chroma collection '{index.collection_name}' built successfully.")

    print("=== Step 4: Generating or Loading Test Set ===")
    test_set_path = settings.paths.eval_testset
    if settings.refresh_test_set or not test_set_path.exists():
        test_set = build_test_set(df_clean, output_path=test_set_path)
        print(f"Generated new evaluation test set with {len(test_set)} samples at {test_set_path}.")
    else:
        test_set = read_json(test_set_path)
        print(f"Loaded existing evaluation test set with {len(test_set)} samples from {test_set_path}.")

    print("=== Step 5: Evaluating Baseline Pipeline ===")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=test_set_path,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print("Baseline Metrics Summary:", bundle.summary)

    print("=== Step 6: Data Observability - Quality Checks & Freshness Report ===")
    quality = run_data_quality_checks(df_clean, settings, report_name="baseline_quality")
    freshness = build_freshness_report(df_clean, settings, report_path=settings.paths.freshness_report)

    print("=== Step 7: Generating Baseline Markdown Report ===")
    source_summary = {
        "total_records": len(records),
        "source_name": settings.source_api,
        "query": settings.source_query,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )
    print(f"Phase 1 report saved to {settings.paths.baseline_report}.")

    print("=== Step 8: Running Demo Agent Q&A ===")
    demo_sample_q = "What is the summary of the paper 'agentic retrieval augmented generation large language model'?"
    demo_ans = answer_question(demo_sample_q, settings=settings, index=index)
    demo_payload = [
        {
            "question": demo_ans.question,
            "answer": demo_ans.answer,
            "retrieved_doc_ids": demo_ans.retrieved_doc_ids,
        }
    ]
    write_json(settings.paths.demo_answers, demo_payload)
    print(f"Demo answers saved to {settings.paths.demo_answers}.")
    print("=== Phase 1 Baseline Pipeline completed successfully! ===")

