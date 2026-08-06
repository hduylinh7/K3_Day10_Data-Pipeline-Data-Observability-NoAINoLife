from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


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


def _extract_date(date_dict: dict | None) -> str:
    if not date_dict or not isinstance(date_dict, dict):
        return "2024-01-01"
    date_parts = date_dict.get("date-parts", [[]])
    if not date_parts or not date_parts[0]:
        return "2024-01-01"
    parts = date_parts[0]
    year = parts[0] if len(parts) > 0 else 2024
    month = parts[1] if len(parts) > 1 else 1
    day = parts[2] if len(parts) > 2 else 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload into list of PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "")
        paper_id = doi if doi else item.get("id", "")
        if not paper_id:
            continue

        # Extract title
        raw_title = item.get("title", [])
        if isinstance(raw_title, list):
            title = " ".join(raw_title) if raw_title else ""
        else:
            title = str(raw_title or "")

        # Extract summary / abstract
        raw_abstract = item.get("abstract") or item.get("description") or ""

        # Extract authors
        authors: list[str] = []
        for author in item.get("author", []):
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            name = author.get("name", "").strip()
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
            elif name:
                authors.append(name)

        # Extract categories / subject
        categories = [str(sub).strip() for sub in item.get("subject", []) if sub]
        primary_cat = categories[0] if categories else "cs.AI"

        # Extract dates
        published_dict = (
            item.get("published-print")
            or item.get("published-online")
            or item.get("issued")
            or item.get("created")
        )
        published = _extract_date(published_dict)
        updated = _extract_date(item.get("deposited") or published_dict)

        # Extract URLs
        abs_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        pdf_url = abs_url
        for link in item.get("link", []):
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                pdf_url = link.get("URL", abs_url)
                break

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=raw_abstract,
                authors=authors,
                categories=categories,
                primary_category=primary_cat,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment="",
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch raw records from Crossref API, save raw payload & parsed records."""
    import time
    import dataclasses
    import requests
    from core.utils import write_json

    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    headers = {
        "User-Agent": "DataObservabilityPipeline/1.0 (mailto:student@example.com)"
    }

    max_retries = 3
    backoff_factor = 2
    response_json = None

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                response_json = resp.json()
                break
            elif resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(backoff_factor ** attempt)
            else:
                resp.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(backoff_factor ** attempt)

    if response_json is None:
        raise RuntimeError("Failed to fetch records from Crossref API after retries.")

    # Save raw API response
    write_json(settings.paths.raw_api_response, response_json)

    # Parse records
    records = parse_crossref_payload(response_json)

    # Save raw records json
    records_dict = [dataclasses.asdict(r) for r in records]
    write_json(settings.paths.raw_records_json, records_dict)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Read JSON snapshot and map into list of PaperRecord."""
    from core.utils import read_json

    data = read_json(path)
    records: list[PaperRecord] = []
    for item in data:
        records.append(
            PaperRecord(
                paper_id=item["paper_id"],
                title=item["title"],
                summary=item["summary"],
                authors=item.get("authors", []),
                categories=item.get("categories", []),
                primary_category=item.get("primary_category", "cs.AI"),
                published=item.get("published", "2024-01-01"),
                updated=item.get("updated", "2024-01-01"),
                abs_url=item.get("abs_url", ""),
                pdf_url=item.get("pdf_url", ""),
                comment=item.get("comment", ""),
            )
        )
    return records

