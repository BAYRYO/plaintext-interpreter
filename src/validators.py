from .interfaces import IFaviconValidator
from pathlib import Path

class ICOValidator(IFaviconValidator):
    def validate(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                return header[:2] == b'\x00\x00' and header[2:4] == b'\x01\x00'
        except Exception:
            return False

class PNGValidator(IFaviconValidator):
    def validate(self, file_path: Path) -> bool:
        try:
            with open(file_path, 'rb') as f:
                return f.read(8) == b'\x89PNG\r\n\x1a\n'
        except Exception:
            return False

class SVGValidator(IFaviconValidator):
    def validate(self, file_path: Path) -> bool:
        try:
            content = file_path.read_text()
            return '<svg' in content.lower() and '</svg>' in content.lower()
        except Exception:
            return False

class ValidatorFactory:
    _validators = {
        '.ico': ICOValidator(),
        '.png': PNGValidator(),
        '.svg': SVGValidator()
    }

    @classmethod
    def get_validator(cls, file_extension: str) -> IFaviconValidator:
        return cls._validators.get(file_extension.lower())
