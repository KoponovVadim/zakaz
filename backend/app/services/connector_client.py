from urllib.parse import urlencode

import httpx

from app.services.connector_signature import sign_request

CONNECTOR_FILES = ("leadhub-connector.php", "lh.php")


def connector_url(base_url: str, params: dict[str, str | int], connector_file: str = "leadhub-connector.php") -> str:
    return base_url.rstrip("/") + "/" + connector_file + "?" + urlencode(params)


def connector_error(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            code = data.get("code") or "connector_error"
            message = data.get("message") or data.get("status") or response.text
            return f"{response.status_code} {code}: {message}"
    except ValueError:
        pass
    text = response.text.strip()
    if len(text) > 500:
        text = text[:500] + "..."
    return f"{response.status_code}: {text or response.reason_phrase}"


async def call_connector(base_url: str, secret: str, site_uid: str, action: str, **extra):
    ts, sig = sign_request(
        secret=secret,
        action=action,
        site_uid=site_uid,
        type_=extra.get("type"),
        since_id=str(extra.get("since_id", "0")),
    )
    params = {"action": action, "site_uid": site_uid, "ts": ts, "sig": sig}
    params.update({k: v for k, v in extra.items() if v is not None})
    errors = []
    async with httpx.AsyncClient(timeout=20) as client:
        for connector_file in CONNECTOR_FILES:
            response = await client.get(connector_url(base_url, params, connector_file))
            if response.status_code < 400:
                data = response.json()
                if isinstance(data, dict):
                    data.setdefault("connector_file", connector_file)
                return data

            error = connector_error(response)
            errors.append(f"{connector_file}: {error}")

            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                raise RuntimeError(error)

        raise RuntimeError("; ".join(errors))
