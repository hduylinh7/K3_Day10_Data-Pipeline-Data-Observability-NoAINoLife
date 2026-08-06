from dataclasses import asdict
from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw PaperRecord objects into a DataFrame ready for embedding and indexing."""
    rows = []
    run_dt_date = run_date.date() if isinstance(run_date, datetime) else run_date

    for r in records:
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)
        if not title or not summary:
            continue

        authors = [normalize_whitespace(a) for a in r.authors if normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in r.categories if normalize_whitespace(c)]

        pub_str = r.published[:10] if r.published else "2024-01-01"
        try:
            pub_date = datetime.strptime(pub_str, "%Y-%m-%d").date()
        except ValueError:
            pub_date = run_dt_date
            pub_str = pub_date.isoformat()

        age_days = max(0, (run_dt_date - pub_date).days)
        authors_joined = compact_join(authors, sep=", ") or "Unknown Author"
        categories_joined = compact_join(categories, sep=", ") or "General"
        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {pub_str}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        row = {
            "paper_id": r.paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "primary_category": r.primary_category,
            "published": pub_str,
            "updated": r.updated[:10] if r.updated else pub_str,
            "abs_url": r.abs_url,
            "pdf_url": r.pdf_url,
            "comment": r.comment,
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": summary_chars,
            "age_days": age_days,
            "text_for_embedding": text_for_embedding,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    # Drop duplicates by paper_id keeping first occurrence
    df = df.drop_duplicates(subset=["paper_id"], keep="first").reset_index(drop=True)
    # Sort by published descending
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df

