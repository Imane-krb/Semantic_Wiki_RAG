"""
MediaWiki Data Ingestion Module.

Fetches all pages from the MediaWiki instance via its API,
parses structured templates (Article, Author, Institution, Keyword),
and produces rich text documents ready for embedding.

Uses concurrent requests for faster fetching.
"""

import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from src.config import MEDIAWIKI_API, MEDIAWIKI_URL


class MediaWikiIngester:
    """Fetches and parses structured content from MediaWiki."""

    def __init__(self, api_url: str = MEDIAWIKI_API, max_workers: int = 10):
        self.api_url = api_url
        self.session = requests.Session()
        self.max_workers = max_workers

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def fetch_all_documents(self) -> List[Dict]:
        """
        Fetch all pages and return a list of parsed document dicts.

        Each dict has:
            - page_title: str
            - page_id: int
            - entity_type: str  ('article', 'author', 'institution', 'keyword', 'unknown')
            - metadata: dict    (structured fields from the template)
            - text: str         (rich text representation for embedding)
            - source_url: str   (link back to the wiki page)
        """
        titles = self._get_all_page_titles()
        print(f"[Ingestion] Found {len(titles)} pages. Fetching content...")

        documents = []
        failed = 0

        # Use thread pool for concurrent fetching
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_page, title): title
                for title in titles
            }

            for i, future in enumerate(as_completed(futures), 1):
                if i % 50 == 0 or i == len(titles):
                    print(f"[Ingestion] Progress: {i}/{len(titles)} pages processed")
                try:
                    doc = future.result()
                    if doc and doc["text"].strip():
                        documents.append(doc)
                except Exception:
                    failed += 1

        print(f"[Ingestion] Done: {len(documents)} documents extracted, "
              f"{failed} failed.")
        return documents

    # ──────────────────────────────────────────
    # Internal: Page Listing
    # ──────────────────────────────────────────

    def _get_all_page_titles(self) -> List[str]:
        """Retrieve all page titles via the allpages API (with retries)."""
        import time as _time

        titles = []
        params = {
            "action": "query",
            "list": "allpages",
            "aplimit": "500",
            "format": "json",
        }
        continue_token = None

        while True:
            if continue_token:
                params["apcontinue"] = continue_token

            # Retry loop for each batch request
            resp = None
            for attempt in range(3):
                try:
                    resp = self.session.get(self.api_url, params=params, timeout=30)
                    break
                except Exception as e:
                    if attempt < 2:
                        print(f"[Ingestion] Retry {attempt+1}/3 for page listing...")
                        _time.sleep(2 * (attempt + 1))
                    else:
                        raise ConnectionError(
                            f"Cannot connect to MediaWiki at {self.api_url}. "
                            f"Please check that the server is running and reachable. "
                            f"Error: {e}"
                        )

            data = resp.json()
            pages = data.get("query", {}).get("allpages", [])
            titles.extend(p["title"] for p in pages)

            if "continue" in data:
                continue_token = data["continue"].get("apcontinue")
            else:
                break

        return titles

    # ──────────────────────────────────────────
    # Internal: Page Processing
    # ──────────────────────────────────────────

    def _process_page(self, title: str, retries: int = 3) -> Optional[Dict]:
        """Fetch wikitext for a page and parse it into a document (with retries)."""
        import time as _time

        for attempt in range(retries):
            try:
                params = {
                    "action": "parse",
                    "page": title,
                    "prop": "wikitext",
                    "format": "json",
                }
                resp = requests.get(self.api_url, params=params, timeout=15)
                data = resp.json()
                break  # success
            except Exception:
                if attempt < retries - 1:
                    _time.sleep(1 * (attempt + 1))  # backoff
                    continue
                return None
        else:
            return None

        try:

            if "error" in data:
                return None

            page_id = data["parse"]["pageid"]
            wikitext = data["parse"]["wikitext"]["*"]

            entity_type, metadata = self._parse_template(wikitext)
            text = self._build_text(entity_type, metadata, title)
            source_url = f"{MEDIAWIKI_URL}/index.php/{title.replace(' ', '_')}"

            return {
                "page_title": title,
                "page_id": page_id,
                "entity_type": entity_type,
                "metadata": metadata,
                "text": text,
                "source_url": source_url,
            }

        except Exception:
            return None

    # ──────────────────────────────────────────
    # Internal: Template Parsing
    # ──────────────────────────────────────────

    def _parse_template(self, wikitext: str) -> tuple:
        """
        Detect the template type and extract key-value pairs.
        Returns (entity_type, metadata_dict).
        """
        wikitext_lower = wikitext.lower()

        if "{{article" in wikitext_lower:
            return "article", self._extract_fields(wikitext)
        elif "{{author" in wikitext_lower or "{{ author" in wikitext_lower:
            return "author", self._extract_fields(wikitext)
        elif "{{institution" in wikitext_lower:
            return "institution", self._extract_fields(wikitext)
        elif "{{keyword" in wikitext_lower:
            return "keyword", self._extract_keyword(wikitext)
        else:
            return "unknown", {"raw": wikitext.strip()}

    def _extract_fields(self, wikitext: str) -> Dict:
        """Extract |Key=Value pairs from a MediaWiki template."""
        fields = {}
        # Match |FieldName=Value patterns, handling multi-line values
        pattern = r'\|(\w[\w\s]*\w|\w)\s*=\s*(.*?)(?=\n\s*\||\n\s*\}\}|$)'
        matches = re.findall(pattern, wikitext, re.DOTALL)

        for key, value in matches:
            key = key.strip()
            value = value.strip()
            if value and value.lower() != "none":
                fields[key] = value

        return fields

    def _extract_keyword(self, wikitext: str) -> Dict:
        """Extract keyword name from {{keyword|name=...}}."""
        match = re.search(r'\|name\s*=\s*([^}]+)', wikitext)
        name = match.group(1).strip() if match else ""
        return {"name": name}

    # ──────────────────────────────────────────
    # Internal: Text Building
    # ──────────────────────────────────────────

    def _build_text(self, entity_type: str, metadata: Dict, title: str) -> str:
        """
        Build a rich text representation suitable for embedding.
        Combines the structured metadata into a natural-language paragraph.
        """
        if entity_type == "article":
            return self._build_article_text(metadata, title)
        elif entity_type == "author":
            return self._build_author_text(metadata, title)
        elif entity_type == "institution":
            return self._build_institution_text(metadata, title)
        elif entity_type == "keyword":
            name = metadata.get("name", title)
            return f"Keyword: {name}. This is a research keyword/topic used in the knowledge base."
        else:
            return metadata.get("raw", title)

    def _build_article_text(self, meta: Dict, title: str) -> str:
        """Build text for an Article entity."""
        parts = []

        article_title = meta.get("Articletitle", title)
        parts.append(f"Research Article: {article_title}")

        if meta.get("Abstract"):
            parts.append(f"Abstract: {meta['Abstract']}")

        if meta.get("Author"):
            parts.append(f"Authors: {meta['Author']}")

        if meta.get("PublicationDate"):
            parts.append(f"Publication Date: {meta['PublicationDate']}")

        if meta.get("PublishedIn"):
            parts.append(f"Published In: {meta['PublishedIn']}")

        if meta.get("Keyword"):
            parts.append(f"Keywords: {meta['Keyword']}")

        if meta.get("Field"):
            parts.append(f"Field: {meta['Field']}")

        if meta.get("Subfield"):
            parts.append(f"Subfield: {meta['Subfield']}")

        if meta.get("DOI"):
            parts.append(f"DOI: {meta['DOI']}")

        if meta.get("CitedByCount"):
            parts.append(f"Cited By: {meta['CitedByCount']} papers")

        if meta.get("FWCI"):
            parts.append(f"Field-Weighted Citation Impact (FWCI): {meta['FWCI']}")

        if meta.get("Topic"):
            parts.append(f"Topic: {meta['Topic']}")

        return "\n".join(parts)

    def _build_author_text(self, meta: Dict, title: str) -> str:
        """Build text for an Author entity."""
        parts = []

        name = meta.get("FullName", title)
        parts.append(f"Researcher: {name}")

        if meta.get("institution"):
            parts.append(f"Affiliated Institutions: {meta['institution']}")

        if meta.get("Current affiliation"):
            parts.append(f"Current Affiliation: {meta['Current affiliation']}")

        if meta.get("h_index"):
            parts.append(f"h-index: {meta['h_index']}")

        if meta.get("i10_index"):
            parts.append(f"i10-index: {meta['i10_index']}")

        if meta.get("WorkCount"):
            parts.append(f"Number of Works: {meta['WorkCount']}")

        if meta.get("orcid") and meta["orcid"].lower() != "none":
            parts.append(f"ORCID: {meta['orcid']}")

        return "\n".join(parts)

    def _build_institution_text(self, meta: Dict, title: str) -> str:
        """Build text for an Institution entity."""
        parts = []

        name = meta.get("InstitutionName", title)
        parts.append(f"Institution: {name}")

        if meta.get("InstitutionCountry"):
            parts.append(f"Country: {meta['InstitutionCountry']}")

        if meta.get("InstitutionType"):
            parts.append(f"Type: {meta['InstitutionType']}")

        return "\n".join(parts)
