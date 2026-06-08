import hashlib
import hmac
import time


def sign_request(secret: str, action: str, site_uid: str, ts: int | None = None, type_: str | None = None, since_id: str | None = None) -> tuple[int, str]:
    timestamp = ts or int(time.time())
    parts = [site_uid, action]
    if action == "sync":
        parts.extend([type_ or "all", since_id or "0"])
    parts.append(str(timestamp))
    payload = "".join(parts)
    signature = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return timestamp, signature
