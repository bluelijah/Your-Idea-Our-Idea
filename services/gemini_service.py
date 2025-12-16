import google.generativeai as genai
from typing import List, Dict
import json
import re

class GeminiService:
    """Service for interacting with Google Gemini API"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    @staticmethod
    def strip_html_tags(text: str) -> str:
        if not text:
            return text
        return re.sub(r'<[^>]+>', '', text)

    def generate_search_queries(self, idea: str) -> List[str]:
        prompt = f"""You are helping to find the BIGGEST, most well-known competitors to a user's idea.

User's Idea:
{idea}

Task: Generate 7-10 search queries that will find the OFFICIAL WEBSITES of the TOP major brands/companies that already do this.

Rules:
- Use ONLY company names
- Use household names only
- No generic terms

Respond in JSON:
{{ "queries": ["Instagram", "Facebook", "Snapchat"] }}
"""
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text).get("queries", [idea])
        except Exception:
            return [idea]

    def analyze_idea_uniqueness(self, idea: str, search_results: List[Dict]) -> Dict:
        search_context = "\n\n".join([
            f"Title: {r['title']}\nDescription: {r['description']}\nURL: {r['url']}"
            for r in search_results[:5]
        ])

        prompt = f"""Determine whether this idea is unique.

Idea:
{idea}

Search Results:
{search_context if search_results else "None"}

Rules:
- NOT unique only if results clearly implement the same idea
- Generic or unrelated results do NOT count
- If no clear implementation exists → unique

Respond in JSON:
{{ "is_unique": true/false, "reasoning": "..." }}
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text)
        except Exception:
            return {
                "is_unique": True,
                "reasoning": "No clear implementation found."
            }

    def is_generic_idea(self, idea: str) -> bool:
        """
        Detects whether an idea is a well-known, already-solved product category
        """
        prompt = f"""Classify this product idea.

Idea:
{idea}

Return TRUE only if this EXACT idea is a well-known, common product category that already exists
in the market (e.g., "a social media app", "a ride sharing service", "a food delivery app").

Return FALSE if:
- The idea contains futuristic/impossible technology (telepathic, teleportation, time travel, etc.)
- The idea is highly specific or novel
- The idea combines existing concepts in a new way
- The idea is absurd or nonsensical

Examples:
- "A social media app" → TRUE (generic, already exists)
- "A telepathic painting device" → FALSE (futuristic technology, doesn't exist)
- "An app for sharing photos" → TRUE (Instagram exists)
- "A pizza delivery drone with AI" → FALSE (specific/novel combination)

Respond in JSON:
{{ "is_generic": true/false }}
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text).get("is_generic", False)
        except Exception:
            return True  # fail-safe

    def generate_fake_projects(self, idea: str, count: int = 3) -> List[Dict]:
        prompt = f"""Create {count} fictional companies that claim to have built this idea.

Idea:
{idea}

Respond in JSON:
{{ "projects": [{{"title":"...","description":"...","status":"..."}}] }}
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()

            projects = json.loads(text).get("projects", [])

            for p in projects:
                p["title"] = self.strip_html_tags(p.get("title", ""))
                p["description"] = self.strip_html_tags(p.get("description", ""))
                p["status"] = self.strip_html_tags(p.get("status", ""))

            return projects
        except Exception:
            return [{
                "title": "Confidential Industry Project",
                "description": "A private company has patented a similar concept.",
                "status": "Patented (details confidential)"
            }]
