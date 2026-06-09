from urllib.parse import urlencode

import httpx

from app.services.connector_signature import sign_request

CONNECTOR_FILES = ("leadhub-connector.php", "lh.php")
CONNECTOR_HEADERS = {
    "User-Agent": "ZakazDeluxMediaConnector/1.0",
    "Accept": "application/json",
    "Cookie": "beget=begetok",
}


def connector_url(base_url: str, params: dict[str, str | int], connector_file: str = "leadhub-connector.php") -> str:
    return base_url.rstrip("/") + "/" + connector_file + "?" + urlencode(params)


def response_body_preview(response: httpx.Response) -> str:
    text = response.text.strip()
    if len(text) > 500:
        text = text[:500] + "..."
    return text


def connector_response_details(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    return (
        f"status_code={response.status_code}, "
        f"content_type={content_type or 'unknown'}, "
        f"body={response_body_preview(response) or response.reason_phrase}"
    )


def connector_error(response: httpx.Response, data: object | None = None) -> str:
    if isinstance(data, dict):
        code = data.get("code") or "connector_error"
        message = data.get("message") or data.get("status") or response.text
        return f"{response.status_code} {code}: {message}"

    try:
        parsed = response.json()
        if isinstance(parsed, dict):
            code = parsed.get("code") or "connector_error"
            message = parsed.get("message") or parsed.get("status") or response.text
            return f"{response.status_code} {code}: {message}"
    except ValueError:
        pass

    text = response_body_preview(response)
    return f"{response.status_code}: {text or response.reason_phrase}"


def is_json_response(response: httpx.Response) -> bool:
    return "application/json" in response.headers.get("content-type", "").lower()


def parse_connector_json(response: httpx.Response) -> object:
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Connector returned invalid JSON response ({connector_response_details(response)})") from exc


async def request_connector_json(client: httpx.AsyncClient, url: str) -> tuple[httpx.Response, object]:
    response = await client.get(url, headers=CONNECTOR_HEADERS)
    if is_json_response(response):
        return response, parse_connector_json(response)

    if "beget=begetok" in response.text:
        response = await client.get(url, headers={**CONNECTOR_HEADERS, "Cookie": "beget=begetok"})
        if is_json_response(response):
            return response, parse_connector_json(response)

    raise RuntimeError(f"Connector returned non-JSON response ({connector_response_details(response)})")


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
            try:
                response, data = await request_connector_json(client, connector_url(base_url, params, connector_file))
            except RuntimeError as exc:
                errors.append(f"{connector_file}: {exc}")
                continue

            if response.status_code < 400 or response.status_code == 403:
                if isinstance(data, dict):
                    data.setdefault("connector_file", connector_file)
                return data

            error = connector_error(response, data)
            errors.append(f"{connector_file}: {error}")
            raise RuntimeError(error)

        raise RuntimeError("; ".join(errors))
