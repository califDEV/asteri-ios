"""Validate private configuration before upstream Starlark generation."""
import json
import re


def validate_config(raw, mode):
    if mode not in {"unsigned", "signed", "simulator"}:
        raise ValueError("Unknown build mode")
    if not raw:
        raise ValueError("Set the TELEGRAM_BUILD_CONFIGURATION GitHub Actions secret")
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        raise ValueError("Build configuration must be valid JSON") from None
    if not isinstance(value, dict):
        raise ValueError("Build configuration must be a JSON object")
    patterns = {
        "bundle_id": r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",
        "api_id": r"[1-9][0-9]*",
        "api_hash": r"[a-fA-F0-9]{32}",
        "team_id": r"[A-Z0-9]{10}",
        "is_internal_build": r"(?:true|false)",
        "is_appstore_build": r"false",
        "appstore_id": r"0",
        "app_specific_url_scheme": r"[a-z][a-z0-9+.-]*",
        "premium_iap_product_id": r"[A-Za-z0-9_.-]*",
    }
    for key, pattern in patterns.items():
        if not isinstance(value.get(key), str) or not re.fullmatch(pattern, value[key]):
            raise ValueError(f"Invalid or missing {key}")
    for key in ("enable_siri", "enable_icloud"):
        if type(value.get(key)) is not bool:
            raise ValueError(f"{key} must be a JSON boolean")
    if value["api_id"] == "8" or value["bundle_id"] == "ph.telegra.Telegraph":
        raise ValueError("Use your own Telegram API ID and an independent bundle ID")
    if mode == "signed" and value["team_id"] == "UNSIGNED00":
        raise ValueError("Signed mode requires your actual Apple Team ID")
    return {key: value[key] for key in (*patterns, "enable_siri", "enable_icloud")}
