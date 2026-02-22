"""
Authentication module for Azure DevOps.

Uses azure-identity (AzureCliCredential / DefaultAzureCredential) to obtain
OAuth tokens for ADO, with an in-memory + file cache to avoid repeated
interactive flows.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from azure.identity import AzureCliCredential, DefaultAzureCredential

# ADO REST API resource scope
_ADO_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798/.default"

# Cache file lives next to the package
_CACHE_DIR = Path(os.environ.get("ADO_SKILL_CACHE_DIR", Path.home() / ".cache" / "ado-skill"))
_CACHE_FILE = _CACHE_DIR / "token_cache.json"

# In-memory singleton
_cached_token: Optional[dict] = None


def _load_cache() -> Optional[dict]:
    """Load cached token from disk if still valid."""
    try:
        if _CACHE_FILE.exists():
            data = json.loads(_CACHE_FILE.read_text())
            # Keep a 5-minute buffer before expiry
            if data.get("expires_on", 0) > time.time() + 300:
                return data
    except Exception:
        pass
    return None


def _save_cache(token_data: dict) -> None:
    """Persist token to disk."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(token_data))
        _CACHE_FILE.chmod(0o600)
    except Exception:
        pass


def get_token() -> str:
    """Return a valid OAuth access token for Azure DevOps.

    Resolution order:
    1. In-memory cache
    2. Disk cache
    3. AzureCliCredential (az login)
    4. DefaultAzureCredential (managed identity, etc.)
    """
    global _cached_token

    # 1. In-memory cache
    if _cached_token and _cached_token["expires_on"] > time.time() + 300:
        return _cached_token["token"]

    # 2. Disk cache
    disk = _load_cache()
    if disk:
        _cached_token = disk
        return disk["token"]

    # 3. AzureCliCredential first (fast when user has done `az login`)
    for cred_cls in (AzureCliCredential, DefaultAzureCredential):
        try:
            cred = cred_cls()
            access = cred.get_token(_ADO_RESOURCE)
            token_data = {"token": access.token, "expires_on": access.expires_on}
            _cached_token = token_data
            _save_cache(token_data)
            return access.token
        except Exception:
            continue

    raise RuntimeError(
        "Unable to authenticate with Azure DevOps. "
        "Run `az login` to sign in."
    )
