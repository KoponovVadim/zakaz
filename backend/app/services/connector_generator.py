from pathlib import Path

from app.core.config import settings


def template_root() -> Path:
    current = Path(__file__).resolve()
    candidates = [
        Path("/app/connectors/templates"),
        current.parents[2] / "connectors" / "templates",
        current.parents[3] / "connectors" / "templates",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def render_connector(joomla_version: str, site_uid: str, secret: str) -> str:
    template_path = template_root() / f"joomla{joomla_version}" / "leadhub-connector.php.tpl"
    if not template_path.exists():
        raise FileNotFoundError(f"Connector template not found: {template_path}")
    content = template_path.read_text(encoding="utf-8")
    return (
        content.replace("{{SITE_UID}}", site_uid)
        .replace("{{SECRET}}", secret)
        .replace("{{CONNECTOR_VERSION}}", settings.connector_version)
        .replace("{{TARGET_JOOMLA_VERSION}}", joomla_version)
    )
