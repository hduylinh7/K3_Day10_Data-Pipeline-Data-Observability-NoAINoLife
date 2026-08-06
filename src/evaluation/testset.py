from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | None = None) -> list[dict[str, Any]]:
    """Build evaluation test set from cleaned DataFrame and optionally save to output_path."""
    if df.empty:
        raise ValueError("Cannot build test set from an empty DataFrame.")

    test_set: list[dict[str, Any]] = []
    sample_size = min(len(df), 10)
    sampled_df = df.iloc[:sample_size]

    q_idx = 1
    for _, row in sampled_df.iterrows():
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        authors_joined = str(row["authors_joined"])
        published = str(row["published"])
        categories_joined = str(row["categories_joined"])
        summary = str(row["summary"])

        # Summary question
        test_set.append(
            {
                "id": f"eval-{q_idx}",
                "question_type": "summary",
                "question": f"What is the summary of the paper '{title}'?",
                "ground_truth": first_sentence(summary),
                "ground_truth_doc_ids": [paper_id],
            }
        )
        q_idx += 1

        # Authors question
        test_set.append(
            {
                "id": f"eval-{q_idx}",
                "question_type": "authors",
                "question": f"Who authored the paper '{title}'?",
                "ground_truth": authors_joined,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        q_idx += 1

        # Publication Date question
        test_set.append(
            {
                "id": f"eval-{q_idx}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        q_idx += 1

        # Categories question
        test_set.append(
            {
                "id": f"eval-{q_idx}",
                "question_type": "categories",
                "question": f"What categories belong to the paper '{title}'?",
                "ground_truth": categories_joined,
                "ground_truth_doc_ids": [paper_id],
            }
        )
        q_idx += 1

    if output_path:
        write_json(Path(output_path), test_set)

    return test_set

