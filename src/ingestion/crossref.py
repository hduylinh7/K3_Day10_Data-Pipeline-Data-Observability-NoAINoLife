from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_html(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(cleaned)


def _extract_date(item: dict[str, Any]) -> str:
    for date_key in ("published-online", "published-print", "issued", "created"):
        dp = item.get(date_key, {}).get("date-parts", [[]])
        if dp and dp[0]:
            parts = dp[0]
            year = parts[0] if len(parts) > 0 else 2024
            month = parts[1] if len(parts) > 1 else 1
            day = parts[2] if len(parts) > 2 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
    return "2024-01-01"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into a list of PaperRecord objects."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []
    for item in items:
        doi = item.get("DOI", "").strip()
        if not doi:
            continue
        titles = item.get("title", [])
        title = _clean_html(titles[0]) if titles else ""
        if not title:
            continue

        abstract = item.get("abstract", "")
        summary = _clean_html(abstract)
        if not summary:
            summary = title

        authors_raw = item.get("author", [])
        authors: list[str] = []
        for a in authors_raw:
            name = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if name:
                authors.append(name)
        if not authors:
            authors = ["Unknown Author"]

        categories = [str(cat).strip() for cat in item.get("subject", []) if str(cat).strip()]
        if not categories:
            categories = ["General"]
        primary_category = categories[0]

        published = _extract_date(item)
        updated = published

        abs_url = item.get("URL", f"https://doi.org/{doi}")
        pdf_url = abs_url
        for link in item.get("link", []):
            if link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", abs_url)
                break

        comment = str(item.get("publisher", ""))

        records.append(
            PaperRecord(
                paper_id=doi,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch source records from Crossref API or load cached raw records."""
    raw_api_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    if not settings.refresh_source and raw_records_path.exists():
        return load_raw_records(raw_records_path)

    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {"User-Agent": "DataPipelineLab/1.0 (mailto:lab@example.com)"}

    payload = None
    max_retries = 3
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = requests.get("https://api.crossref.org/works", params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                payload = response.json()
                break
            if response.status_code in (429, 503):
                time.sleep(backoff)
                backoff *= 2.0
            else:
                response.raise_for_status()
        except Exception as e:
            if attempt == max_retries - 1:
                if raw_records_path.exists():
                    return load_raw_records(raw_records_path)
                raise e
            time.sleep(backoff)
            backoff *= 2.0

    if payload is None:
        if raw_records_path.exists():
            return load_raw_records(raw_records_path)
        raise RuntimeError("Failed to fetch payload from Crossref API.")

    write_json(raw_api_path, payload)
    records = parse_crossref_payload(payload)
    records_as_dicts = [asdict(r) for r in records]
    write_json(raw_records_path, records_as_dicts)
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load JSON raw record snapshot and map to PaperRecord objects."""
    data = read_json(path)
    records: list[PaperRecord] = []
    for item in data:
        records.append(PaperRecord(**item))
    return records

