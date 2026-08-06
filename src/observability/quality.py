from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run data quality validation rules against DataFrame and save results."""
    total_rows = len(df)

    paper_id_nulls = int(df["paper_id"].isna().sum()) if "paper_id" in df.columns else total_rows
    paper_id_duplicates = int(df["paper_id"].duplicated().sum()) if "paper_id" in df.columns else 0
    title_nulls = int(df["title"].isna().sum()) if "title" in df.columns else total_rows

    if "summary" in df.columns:
        summary_short_rows = int((df["summary"].isna() | (df["summary"].str.len() < 20)).sum())
    else:
        summary_short_rows = total_rows

    if "age_days" in df.columns:
        stale_date_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_date_rows = 0

    checks = {
        "min_row_count": {
            "passed": total_rows > 0,
            "actual": total_rows,
            "expected": "> 0",
        },
        "paper_id_not_null": {
            "passed": paper_id_nulls == 0,
            "actual": paper_id_nulls,
            "expected": "0",
        },
        "paper_id_unique": {
            "passed": paper_id_duplicates == 0,
            "actual": paper_id_duplicates,
            "expected": "0",
        },
        "title_not_null": {
            "passed": title_nulls == 0,
            "actual": title_nulls,
            "expected": "0",
        },
        "summary_sufficient_length": {
            "passed": summary_short_rows == 0,
            "actual": summary_short_rows,
            "expected": "0 short or null summaries",
        },
        "freshness_threshold": {
            "passed": stale_date_rows == 0,
            "actual": stale_date_rows,
            "expected": f"0 rows older than {settings.freshness_threshold_days} days",
        },
    }

    all_passed = all(check["passed"] for check in checks.values())

    report = {
        "report_name": report_name,
        "timestamp": now_utc().isoformat(),
        "total_rows": total_rows,
        "all_passed": all_passed,
        "checks": checks,
    }

    out_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(out_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    """Aggregate freshness metrics and write JSON freshness report."""
    total_rows = len(df)
    if total_rows > 0 and "published" in df.columns:
        latest_published = str(df["published"].max())
        oldest_published = str(df["published"].min())
    else:
        latest_published = "N/A"
        oldest_published = "N/A"

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    fresh_rows = total_rows - stale_rows
    is_fresh = stale_rows == 0 and total_rows > 0

    report = {
        "timestamp": now_utc().isoformat(),
        "total_rows": total_rows,
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "stale_rows": stale_rows,
        "fresh_rows": fresh_rows,
        "is_fresh": is_fresh,
    }

    write_json(Path(report_path), report)
    return report

