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
        """Remove HTML tags from text"""
        if not text:
            return text
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        return clean_text

    def generate_search_queries(self, idea: str) -> List[str]:
        """
        Generate optimized search queries from a user's idea description

        Args:
            idea: The user's idea text

        Returns:
            List of search query strings optimized for finding existing implementations
        """
        prompt = f"""You are helping to find the BIGGEST, most well-known competitors to a user's idea.

User's Idea:
{idea}

Task: Generate 7-10 search queries that will find the OFFICIAL WEBSITES of the TOP major brands/companies that already do this.

CRITICAL RULES:
1. ONLY include searches for MAJOR, well-known brands (worth $1B+, millions of users)
2. Search for the company name directly - like "Instagram", "Facebook", "Uber", "Airbnb"
3. Include industry leaders and household names only
4. Think: What are the BIGGEST platforms/apps that already do something similar?

For example, if the idea is "a social media app to share photos with friends":
- "Instagram"
- "Facebook"
- "Snapchat"
- "TikTok"
- "Pinterest"
- "Twitter"
- "BeReal official website"

If the idea is "ride sharing service":
- "Uber"
- "Lyft"
- "Via rideshare"

If the idea is "vacation rentals":
- "Airbnb"
- "VRBO"
- "Booking.com"

Think of the BIGGEST household names first. DO NOT include generic terms or small apps.

Respond in JSON format:
{{
  "queries": ["CompanyName1", "CompanyName2", "CompanyName3", ...]
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Try to parse JSON from response
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()

            result = json.loads(result_text)
            return result.get("queries", [idea])  # Fallback to original idea if parsing fails

        except Exception as e:
            print(f"Error generating search queries: {e}")
            # Fallback to original idea
            return [idea]

    def analyze_idea_uniqueness(self, idea: str, search_results: List[Dict]) -> Dict:
        """
        Analyze if an idea is unique based on search results

        Args:
            idea: The user's idea text
            search_results: List of search results from Brave Search

        Returns:
            Dictionary with 'is_unique' boolean and 'reasoning' string
        """
        # Format search results for the prompt
        search_context = "\n\n".join([
            f"Result {i+1}:\nTitle: {r['title']}\nDescription: {r['description']}\nURL: {r['url']}"
            for i, r in enumerate(search_results[:5])  # Use top 5 results
        ])

        prompt = f"""You are analyzing whether an idea is truly unique and original.

User's Idea:
{idea}

Search Results Found:
{search_context if search_results else "No relevant search results found."}

Task: Determine if this idea is unique.

An idea is considered NOT unique ONLY IF:
- A search result clearly implements the SAME core idea
- The result explicitly describes the same functionality

An idea IS unique if:
- Search results are generic, unrelated, or fallback content
- Results do not clearly match the idea
- No real implementation of this specific concept exists

IMPORTANT RULES:
- Ignore unrelated brands, dictionaries, translation tools, or generic platforms
- If results are not clearly about the idea, treat them as irrelevant
- If no relevant results exist, the idea IS unique

Respond in JSON format:
{{
  "is_unique": true/false,
  "reasoning": "Brief explanation"
}}"""


        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Try to parse JSON from response
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"Error analyzing with Gemini: {e}")
            # Default to not unique if error
            return {
                "is_unique": True,
                "reasoning": "No clear evidence of an existing implementation."
            }

    def generate_fake_projects(self, idea: str, count: int = 3) -> List[Dict]:
        """
        Generate fake projects/websites that claim to have implemented the idea

        Args:
            idea: The user's idea text
            count: Number of fake projects to generate

        Returns:
            List of fake project dictionaries with title, description, and status
        """
        prompt = f"""You are creating fictional but believable project descriptions.

User's Idea:
{idea}

Task: Create {count} fictional projects/companies/websites that claim to have already implemented this idea. Make them sound realistic and professional. Include:
1. A plausible company/project name
2. A convincing description of how they implemented the idea
3. A realistic status (choose from: "Patented by [Company Name]", "Currently in private beta", "Website under construction", "Acquired by [Big Tech Company]", "Launched in [Year]")

Make each one unique and believable. Respond in JSON format:
{{
  "projects": [
    {{
      "title": "Project/Company Name",
      "description": "Detailed description of the implementation",
      "status": "Status message"
    }}
  ]
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Try to parse JSON from response
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()

            result = json.loads(result_text)
            projects = result.get("projects", [])

            # Strip HTML tags from all project fields
            for project in projects:
                if 'title' in project:
                    project['title'] = self.strip_html_tags(project['title'])
                if 'description' in project:
                    project['description'] = self.strip_html_tags(project['description'])
                if 'status' in project:
                    project['status'] = self.strip_html_tags(project['status'])

            return projects

        except Exception as e:
            print(f"Error generating fake projects: {e}")
            # Return generic fake project if error
            return [{
                "title": "Confidential Industry Project",
                "description": f"A private company has patented a similar concept. Due to NDA restrictions, detailed information is not publicly available.",
                "status": "Patented (details confidential)"
            }]
