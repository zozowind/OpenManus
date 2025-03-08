import os
from pathlib import Path
from typing import Optional

import aiofiles
from pydantic import Field

from app.tool import BaseTool

class FileSaver(BaseTool):
    name: str = "file_saver"
    description: str = """Save content to a local file at a specified path.
Use this tool when you need to save text, code, or generated content to a file on the local filesystem.
The tool accepts content and a file path, and saves the content to that location.
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "(required) The content to save to the file.",
            },
            "file_path": {
                "type": "string",
                "description": "(required) The path where the file should be saved, including filename and extension.",
            },
            "mode": {
                "type": "string",
                "description": "(optional) The file opening mode. Default is 'w' for write. Use 'a' for append.",
                "enum": ["w", "a"],
                "default": "w",
            },
        },
        "required": ["content", "file_path"],
    }

    save_path: Optional[str] = Field(None, description="Custom save path for files")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.save_path = kwargs.get("save_path", None)



    def _get_save_path(self, file_path: str) -> Path:
        """
        Get the full save path for a file.
        
        If save_path is configured, the file will be saved relative to that directory.
        Otherwise, the file_path will be used as is.
        """
        if self.save_path:
            base_path = Path(self.save_path)
            base_path.mkdir(parents=True, exist_ok=True)
            return base_path / Path(file_path).name
        return Path(file_path)

    async def execute(self, content: str, file_path: str, mode: str = "w") -> str:
        """
        Save content to a file at the specified path.

        Args:
            content (str): The content to save to the file.
            file_path (str): The path where the file should be saved.
            mode (str, optional): The file opening mode. Default is 'w' for write. Use 'a' for append.

        Returns:
            str: A message indicating the result of the operation.
        """
        try:
            file_path = self._get_save_path(file_path)
            
            # Ensure the parent directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write directly to the file
            async with aiofiles.open(file_path, mode, encoding="utf-8") as file:
                await file.write(content)

            return f"Content successfully saved to {file_path}"
        except Exception as e:
            return f"Error saving file: {str(e)}"
