from __future__ import annotations

from datetime import datetime

import pandas as pd

from ingestion.crossref import PaperRecord


import html
import re

from core.utils import normalize_whitespace


def clean_html_text(text: str) -> str:
    if not text:
        return ""
    # Remove XML / HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Normalize whitespace
    return normalize_whitespace(cleaned)




def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records into a structured DataFrame ready for embedding and indexing."""
    cleaned_rows = []

    for record in records:
        title = clean_html_text(record.title)
        summary = clean_html_text(record.summary)

        # Skip rows with empty title or summary under 100 characters
        if not title or len(summary) < 100:
            continue

        authors_list = record.authors if isinstance(record.authors, list) else []
        authors_joined = ", ".join(authors_list) if authors_list else "Unknown"

        categories_list = record.categories if isinstance(record.categories, list) else []
        categories_joined = ", ".join(categories_list) if categories_list else record.primary_category or "cs.AI"

        # Calculate age_days
        pub_str = str(record.published)[:10] if record.published else "2024-01-01"
        try:
            pub_dt = datetime.strptime(pub_str, "%Y-%m-%d").date()
        except ValueError:
            pub_dt = run_date.date()

        run_d = run_date.date() if hasattr(run_date, "date") else run_date
        age_days = max(0, (run_d - pub_dt).days)

        text_for_embedding = f"Title: {title} | Authors: {authors_joined} | Summary: {summary}"

        cleaned_rows.append(
            {
                "paper_id": record.paper_id,
                "title": title,
                "summary": summary,
                "summary_chars": len(summary),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "primary_category": record.primary_category or "cs.AI",
                "published": pub_str,
                "updated": str(record.updated)[:10] if record.updated else pub_str,
                "age_days": age_days,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(cleaned_rows)
    if df.empty:
        return df

    # Drop duplicates by paper_id and title
    df = df.drop_duplicates(subset=["paper_id"]).drop_duplicates(subset=["title"]).reset_index(drop=True)

    # Sort by published date descending
    df = df.sort_values(by="published", ascending=False).reset_index(drop=True)

    return df

