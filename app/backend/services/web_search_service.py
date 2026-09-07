"""Web Search Service for KisaanDost AI Agronomist.

Retrieves authentic agricultural findings from live web search when local datasets
or baseline models do not contain a specific crop pathogen, dosage, or farming advisory.
"""

from __future__ import annotations

import html
import logging
import re
from typing import Any, Dict, List, Optional
import urllib.parse

import httpx

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(self, timeout_seconds: float = 6.0) -> None:
        self.timeout = timeout_seconds
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5,ur;q=0.3",
        }

    async def search_agronomy(
        self,
        query: str,
        crop: Optional[str] = None,
        district: Optional[str] = None,
        max_results: int = 5,
    ) -> List[Dict[str, str]]:
        """Performs a live web search focused on Punjab / Pakistan agricultural practices."""
        # Craft focused agricultural query
        clean_q = re.sub(r"[^\w\s\-\.]", " ", query).strip()
        enhanced_query = clean_q
        if "punjab" not in clean_q.lower() and "pakistan" not in clean_q.lower():
            enhanced_query = f"Punjab agriculture Pakistan {clean_q}"
        if crop and crop.lower() not in clean_q.lower():
            enhanced_query = f"{enhanced_query} {crop}"

        results: List[Dict[str, str]] = []

        # 1. Try DuckDuckGo HTML Search
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(enhanced_query)}"
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    results = self._parse_duckduckgo_html(resp.text, max_results=max_results)
        except Exception as exc:
            logger.warning("DuckDuckGo search error: %s", exc)

        # 2. If no results, try DuckDuckGo Instant Answers API
        if not results:
            try:
                api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(enhanced_query)}&format=json&no_html=1"
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(api_url, headers=self.headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        abstract = data.get("AbstractText", "").strip()
                        if abstract:
                            results.append({
                                "title": data.get("Heading", "Agricultural Finding"),
                                "snippet": abstract,
                                "source": data.get("AbstractURL", "DuckDuckGo Knowledge"),
                            })
                        for topic in data.get("RelatedTopics", [])[:3]:
                            if isinstance(topic, dict) and "Text" in topic:
                                results.append({
                                    "title": "Related Topic",
                                    "snippet": topic["Text"],
                                    "source": topic.get("FirstURL", "Web Knowledge"),
                                })
            except Exception as exc:
                logger.warning("DuckDuckGo API error: %s", exc)

        return results

    def _parse_duckduckgo_html(self, html_text: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Parses HTML search snippets cleanly."""
        results: List[Dict[str, str]] = []
        raw_snippets = re.findall(
            r'<a class="result__snippet"[^>]*>(.*?)</a>',
            html_text,
            re.DOTALL,
        )
        if not raw_snippets:
            raw_snippets = re.findall(
                r'class="result__snippet"[^>]*>(.*?)<',
                html_text,
                re.DOTALL,
            )

        raw_titles = re.findall(
            r'<a class="result__url"[^>]*>(.*?)</a>',
            html_text,
            re.DOTALL,
        )

        for i, s in enumerate(raw_snippets[:max_results]):
            clean_snippet = re.sub(r"<[^>]+>", "", s)
            clean_snippet = html.unescape(clean_snippet).strip()
            # Remove repeated spaces/newlines
            clean_snippet = re.sub(r"\s+", " ", clean_snippet)

            if len(clean_snippet) > 25:
                title = f"Finding {i + 1}"
                if i < len(raw_titles):
                    clean_title = re.sub(r"<[^>]+>", "", raw_titles[i]).strip()
                    if clean_title:
                        title = clean_title
                results.append({
                    "title": title,
                    "snippet": clean_snippet,
                    "source": "Google / DuckDuckGo Agri Search",
                })

        return results

    def synthesize_summary(self, snippets: List[Dict[str, str]], is_urdu: bool = True) -> str:
        """Synthesizes snippets into a cohesive agronomic advice paragraph."""
        if not snippets:
            return ""

        combined = " ".join(item["snippet"] for item in snippets[:3])
        # Clean citations, URLs, dates
        combined = re.sub(r"https?://\S+", "", combined)
        combined = re.sub(r"\s+", " ", combined).strip()
        return combined


_search_service: Optional[WebSearchService] = None


def get_web_search_service() -> WebSearchService:
    global _search_service
    if _search_service is None:
        _search_service = WebSearchService()
    return _search_service
