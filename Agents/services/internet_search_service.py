"""Internet search service with SerpAPI primary and Tavily fallback."""

from __future__ import annotations

from typing import Any, Dict, List
import requests

from Agents.config import (
    SERPAPI_KEY,
    SERPAPI_BASE_URL,
    TAVILY_API_KEY,
    TAVILY_BASE_URL,
    WEB_SEARCH_TIMEOUT,
)


class InternetSearchService:
    """Performs internet search and returns normalized results."""

    @staticmethod
    def search(query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search with SerpAPI first, then fallback to Tavily."""
        safe_top_k = max(1, min(int(top_k), 10))

        serp_result = InternetSearchService._search_serpapi(query, safe_top_k)
        if serp_result["success"] and serp_result["results"]:
            return {
                **serp_result,
                "provider": "serpapi",
                "provider_used": "serpapi",
                "fallback_used": False,
                "fallback_reason": "",
            }

        fallback_reason = serp_result.get("error", "SerpAPI returned no results.")
        tavily_result = InternetSearchService._search_tavily(query, safe_top_k)
        if tavily_result["success"] and tavily_result["results"]:
            return {
                **tavily_result,
                "provider": "tavily",
                "provider_used": "tavily",
                "fallback_used": True,
                "fallback_reason": fallback_reason,
            }

        combined_error = (
            f"SerpAPI failed: {fallback_reason} | "
            f"Tavily failed: {tavily_result.get('error', 'Unknown error')}"
        )
        return {
            "success": False,
            "query": query,
            "results": [],
            "error": combined_error,
            "provider": "none",
            "provider_used": "none",
            "fallback_used": True,
            "fallback_reason": fallback_reason,
        }

    @staticmethod
    def _search_serpapi(query: str, top_k: int) -> Dict[str, Any]:
        """Run SerpAPI search and normalize organic results."""
        if not SERPAPI_KEY:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": "SERPAPI_KEY is not configured.",
            }

        params = {
            "engine": "google",
            "q": query,
            "num": top_k,
            "hl": "en",
            "api_key": SERPAPI_KEY,
        }
        try:
            response = requests.get(SERPAPI_BASE_URL, params=params, timeout=WEB_SEARCH_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            normalized = InternetSearchService._normalize_serpapi_results(data.get("organic_results", []), top_k)
            if not normalized:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "error": "SerpAPI returned empty organic results.",
                }
            return {
                "success": True,
                "query": query,
                "results": normalized,
                "raw_result_count": len(data.get("organic_results", [])),
            }
        except Exception as exc:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": f"SerpAPI request failed: {str(exc)}",
            }

    @staticmethod
    def _search_tavily(query: str, top_k: int) -> Dict[str, Any]:
        """Run Tavily search and normalize results."""
        if not TAVILY_API_KEY:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": "TAVILY_API_KEY is not configured.",
            }

        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": top_k,
            "include_raw_content": False,
        }
        try:
            response = requests.post(TAVILY_BASE_URL, json=payload, timeout=WEB_SEARCH_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            normalized = InternetSearchService._normalize_tavily_results(data.get("results", []), top_k)
            if not normalized:
                return {
                    "success": False,
                    "query": query,
                    "results": [],
                    "error": "Tavily returned empty results.",
                }
            return {
                "success": True,
                "query": query,
                "results": normalized,
                "raw_result_count": len(data.get("results", [])),
            }
        except Exception as exc:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": f"Tavily request failed: {str(exc)}",
            }

    @staticmethod
    def _normalize_serpapi_results(organic_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Normalize SerpAPI results for consistent UI and response payloads."""
        normalized = []
        for index, item in enumerate(organic_results[:top_k]):
            link = item.get("link", "")
            source = item.get("source", "")
            if not source and link:
                source = InternetSearchService._extract_source_from_url(link)
            normalized.append(
                {
                    "rank": index + 1,
                    "title": item.get("title", "Untitled"),
                    "url": link,
                    "snippet": item.get("snippet", ""),
                    "source": source,
                    "provider": "serpapi",
                }
            )
        return normalized

    @staticmethod
    def _normalize_tavily_results(tavily_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Normalize Tavily results for consistent UI and response payloads."""
        normalized = []
        for index, item in enumerate(tavily_results[:top_k]):
            url = item.get("url", "")
            source = InternetSearchService._extract_source_from_url(url) if url else ""
            normalized.append(
                {
                    "rank": index + 1,
                    "title": item.get("title", "Untitled"),
                    "url": url,
                    "snippet": item.get("content", ""),
                    "source": source,
                    "provider": "tavily",
                }
            )
        return normalized

    @staticmethod
    def _extract_source_from_url(url: str) -> str:
        """Extract readable source label from URL."""
        if "://" in url and len(url.split("/")) > 2:
            return url.split("/")[2]
        return url

    @staticmethod
    def build_context(results: List[Dict[str, Any]]) -> str:
        """Build compact context string from web results."""
        lines = []
        for result in results:
            lines.append(
                f"[{result.get('rank', '?')}] {result.get('title', '')}\n"
                f"Provider: {result.get('provider', '')}\n"
                f"URL: {result.get('url', '')}\n"
                f"Snippet: {result.get('snippet', '')}"
            )
        return "\n\n".join(lines)
