from pathlib import Path

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Execute Phase 2 corruption simulation, evaluation, repair, and comparison flow."""
    print("=== Step 1: Loading Baseline Settings & Clean Data ===")
    settings = load_settings()
    if not settings.paths.clean_csv.exists() or not settings.paths.baseline_metrics.exists():
        raise RuntimeError("Baseline artifacts not found. Please run script/run_phase1.py first.")

    df_baseline = pd.read_csv(settings.paths.clean_csv)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"Loaded baseline clean dataset ({len(df_baseline)} rows) and metrics.")

    print("=== Step 2: Simulating Data Corruption ===")
    df_corrupted = corrupt_clean_dataframe(df_baseline, settings.paths.corruption_log)
    write_csv(df_corrupted, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, df_corrupted.to_dict(orient="records"))
    print(f"Corrupted dataset created ({len(df_corrupted)} rows). Log saved to {settings.paths.corruption_log}.")

    print("=== Step 3: Rebuilding Corrupted Vector Store & Index ===")
    index_corrupted = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    print(f"Corrupted Chroma collection '{index_corrupted.collection_name}' built.")

    print("=== Step 4: Evaluating Corrupted Pipeline ===")
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print("Corrupted Metrics Summary:", corrupted_bundle.summary)

    print("=== Step 5: Data Observability on Corrupted Dataset ===")
    corrupted_quality = run_data_quality_checks(df_corrupted, settings, report_name="corrupted_quality")
    corrupted_freshness = build_freshness_report(
        df_corrupted,
        settings,
        report_path=settings.paths.quality_dir / "corrupted_freshness_report.json",
    )

    print("=== Step 6: Repairing Pipeline from Raw Source ===")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    df_repaired = build_clean_dataframe(raw_records, now_utc())
    write_csv(df_repaired, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, df_repaired.to_dict(orient="records"))
    print(f"Repaired dataset built ({len(df_repaired)} rows). Saved to {settings.paths.repaired_clean_csv}.")

    print("=== Step 7: Rebuilding Repaired Vector Store & Index ===")
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    print(f"Repaired Chroma collection '{index_repaired.collection_name}' built.")

    print("=== Step 8: Evaluating Repaired Pipeline ===")
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    print("Repaired Metrics Summary:", repaired_bundle.summary)

    print("=== Step 9: Data Observability on Repaired Dataset ===")
    repaired_quality = run_data_quality_checks(df_repaired, settings, report_name="repaired_quality")
    repaired_freshness = build_freshness_report(
        df_repaired,
        settings,
        report_path=settings.paths.quality_dir / "repaired_freshness_report.json",
    )

    print("=== Step 10: Generating Corruption & Comparison Report ===")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
    print(f"Comparison report saved to {settings.paths.comparison_report}.")
    print("=== Phase 2 Corruption & Repair Pipeline completed successfully! ===")

