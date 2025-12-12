import requests
from typing import List, Dict

class BraveSearchService:
    """Service for interacting with Brave Search API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    def search(self, query: str, count: int = 10) -> List[Dict]:
        """
        Search for a query using Brave Search API

        Args:
            query: Search query string
            count: Number of results to return (max 20)

        Returns:
            List of search results with title, description, and url
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

        params = {
            "q": query,
            "count": min(count, 20)  # Brave API max is 20
        }

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            if "web" in data and "results" in data["web"]:
                for result in data["web"]["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "description": result.get("description", ""),
                        "url": result.get("url", "")
                    })

            return results

        except requests.exceptions.RequestException as e:
            print(f"Error searching with Brave API: {e}")
            return []
