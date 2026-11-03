import hashlib
import unicodedata


def clean_name(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())


def name_key(value: str) -> str:
    return hashlib.sha256(clean_name(value).casefold().encode("utf-8")).hexdigest()
