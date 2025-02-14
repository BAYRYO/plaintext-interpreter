from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

class IContentProcessor(ABC):
    @abstractmethod
    def process(self, content: str) -> str:
        pass

class IFaviconValidator(ABC):
    @abstractmethod
    def validate(self, file_path: Path) -> bool:
        pass

class ITemplateEngine(ABC):
    @abstractmethod
    def render(self, template_name: str, **kwargs) -> str:
        pass
