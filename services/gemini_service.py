import google.generativeai as genai
from typing import List, Dict
import json

class GeminiService:
    """Service for interacting with Google Gemini API"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

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

Task: Determine if this idea is unique. An idea is considered NOT unique if:
- There's a website, product, or service that implements this exact concept
- There's a patent or company working on this specific idea
- There are blog posts or articles describing this implementation

An idea IS unique if:
- No direct implementations exist (only tangentially related things)
- The search results are generic or unrelated
- No one has built or patented this specific thing

Respond in JSON format:
{{
  "is_unique": true/false,
  "reasoning": "Brief explanation of why it is or isn't unique"
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
                "is_unique": False,
                "reasoning": "Unable to determine uniqueness"
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
            return result.get("projects", [])

        except Exception as e:
            print(f"Error generating fake projects: {e}")
            # Return generic fake project if error
            return [{
                "title": "Confidential Industry Project",
                "description": f"A private company has patented a similar concept. Due to NDA restrictions, detailed information is not publicly available.",
                "status": "Patented (details confidential)"
            }]
