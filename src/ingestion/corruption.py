from pathlib import Path

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate various data corruption scenarios on a cleaned DataFrame and log changes."""
    if df.empty:
        write_json(Path(output_log_path), {"corruptions": []})
        return df.copy()

    cdf = df.copy()
    corruption_log: list[dict] = []
    n = len(cdf)

    # 1. Drop latest 2 records
    drop_count = min(2, n - 1) if n > 2 else 0
    if drop_count > 0:
        dropped_ids = cdf.iloc[:drop_count]["paper_id"].tolist()
        cdf = cdf.iloc[drop_count:].reset_index(drop=True)
        corruption_log.append(
            {
                "type": "drop_latest_records",
                "count": drop_count,
                "paper_ids": [str(pid) for pid in dropped_ids],
            }
        )

    n = len(cdf)
    if n == 0:
        write_json(Path(output_log_path), {"corruptions": corruption_log})
        return cdf

    # 2. Blank summary for row 0 (if exists)
    blank_ids = []
    if n > 0:
        blank_ids.append(str(cdf.at[0, "paper_id"]))
        cdf.at[0, "summary"] = ""
        cdf.at[0, "summary_chars"] = 0

    corruption_log.append({"type": "blank_summary", "paper_ids": blank_ids})

    # 3. Add noise to summary for row 1 (if exists)
    noise_ids = []
    if n > 1:
        noise_ids.append(str(cdf.at[1, "paper_id"]))
        cdf.at[1, "summary"] = "CORRUPTED_NOISE_TEXT " * 10 + str(cdf.at[1, "summary"])
        cdf.at[1, "summary_chars"] = len(cdf.at[1, "summary"])

    corruption_log.append({"type": "inject_noise", "paper_ids": noise_ids})

    # 4. Truncate title for row 2 (if exists)
    truncate_ids = []
    if n > 2:
        truncate_ids.append(str(cdf.at[2, "paper_id"]))
        cdf.at[2, "title"] = str(cdf.at[2, "title"])[:5]

    corruption_log.append({"type": "truncate_title", "paper_ids": truncate_ids})

    # 5. Make date stale for row 3 (if exists)
    stale_ids = []
    if n > 3:
        stale_ids.append(str(cdf.at[3, "paper_id"]))
        cdf.at[3, "published"] = "2020-01-01"
        cdf.at[3, "age_days"] = 2000

    corruption_log.append({"type": "make_stale_date", "paper_ids": stale_ids})

    # 6. Add duplicate rows (duplicate the last row)
    if n > 0:
        dup_row = cdf.iloc[[-1]].copy()
        cdf = pd.concat([cdf, dup_row], ignore_index=True)
        corruption_log.append({"type": "add_duplicate", "paper_id": str(dup_row.iloc[0]["paper_id"])})

    # Rebuild text_for_embedding for all rows
    texts = []
    for _, row in cdf.iterrows():
        text = (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Published: {row['published']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Summary: {row['summary']}"
        )
        texts.append(text)
    cdf["text_for_embedding"] = texts

    write_json(Path(output_log_path), {"corruptions": corruption_log})
    return cdf

