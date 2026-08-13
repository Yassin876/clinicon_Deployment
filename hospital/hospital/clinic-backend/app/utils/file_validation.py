# app/utils/file_validation.py
def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    return file_size <= max_size_mb * 1024 * 1024

def validate_mime_type(mime_type: str, allowed_types: list = None) -> bool:
    if allowed_types is None:
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    return mime_type in allowed_types
