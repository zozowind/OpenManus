import asyncio
from brave import Brave
from typing import List, Optional
from pydantic import Field
from app.tool.base import BaseTool

class BraveSearch(BaseTool):
    name: str = "brave_search"
    description: str = """Perform Brave search and return a list of relevant links.
Recommended for retrieving international information or English content.
The tool returns a list of URLs matching the search query."""
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "(Required) Search keywords to submit to Brave"
            },
            "num_results": {
                "type": "integer",
                "description": "(Optional) Number of search results to return, default is 10",
                "default": 10
            }
        },
        "required": ["query"]
    }
    api_key: Optional[str] = Field(None, description="Brave API key")
    brave: Brave = Field(None, description="Brave client")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = kwargs.get("api_key", None)
        self.brave = Brave(api_key=self.api_key)

    async def execute(self, query: str, num_results: int = 10) -> List[str]:
        """
        Execute Brave search and return a list of URLs

        Args:
            query: Search keywords
            num_results: Number of results to return

        Returns:
            A list of URLs matching the search results
        """
        # Run the search in a thread pool to prevent blocking
        def search(query: str, num_results: int = 10) -> List[str]:
            result = self.brave.search(query, count=num_results)
            links = []
            for result in result.web.results:
                links.append(str(result.url))
            return links

        loop = asyncio.get_event_loop()
        links = await loop.run_in_executor(
            None, lambda: search(query, num_results)
        )
        return links