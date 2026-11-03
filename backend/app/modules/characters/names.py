"""캐릭터 이름 정규화와 중복 검사 키를 생성한다."""
import hashlib
import unicodedata


def clean_name(value: str) -> str:
    """입력한 이름을 정규화한다."""
    return unicodedata.normalize("NFC", value.strip())


def name_key(value: str) -> str:
    """중복 이름 검사용 정규화 키를 생성한다."""
    return hashlib.sha256(clean_name(value).casefold().encode("utf-8")).hexdigest()
