"""
Mini-Ultra Web Search Tool
Simple web search using DuckDuckGo HTML.
"""
import requests
from typing import Any, Dict
from tools.base import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information using DuckDuckGo"

    def execute(self, query: str = "", num_results: int = 5, **kwargs) -> Dict[str, Any]:
        if not query:
            return {"success": False, "error": "No query provided"}

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            resp = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
                timeout=10
            )
            resp.raise_for_status()

            # Simple extraction from HTML results
            results = []
            html = resp.text
            # Extract result snippets between result class markers
            import re
            links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>(.+?)</a>', html)
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.+?)</a>', html)

            for i, (url, title) in enumerate(links[:num_results]):
                snippet = snippets[i] if i < len(snippets) else ""
                # Clean HTML tags
                title = re.sub(r'<[^>]+>', '', title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet
                })

            return {
                "success": True,
                "result": results,
                "query": query,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
