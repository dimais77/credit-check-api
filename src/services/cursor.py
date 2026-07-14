import base64
import binascii
import datetime
import uuid

from core.exceptions import InvalidCursorError


def encode_cursor(checked_at: datetime.datetime, check_id: uuid.UUID) -> str:
    raw = f"{checked_at.isoformat()}|{check_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime.datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        checked_at, check_id = raw.rsplit("|", 1)
        return datetime.datetime.fromisoformat(checked_at), uuid.UUID(check_id)
    except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
        raise InvalidCursorError from exc
