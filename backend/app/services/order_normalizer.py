def normalize_connector_order(raw: dict, source_type: str) -> dict:
    return {
        "source_type": source_type,
        "external_id": str(raw.get("external_id") or raw.get("id")),
        "external_number": raw.get("external_number") or raw.get("number"),
        "customer_name": raw.get("customer_name"),
        "customer_phone": raw.get("customer_phone"),
        "customer_email": raw.get("customer_email"),
        "title": raw.get("title"),
        "message": raw.get("message"),
        "amount": raw.get("amount"),
        "currency": raw.get("currency"),
        "external_status": raw.get("status"),
        "raw_payload": raw,
    }
