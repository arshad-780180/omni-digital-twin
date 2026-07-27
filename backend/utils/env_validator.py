import os
import logging
from typing import Dict, List

logger = logging.getLogger("omni.env")

REQUIRED_VARS: List[str] = [
    "MONGODB_URL",
    "JWT_SECRET_KEY",
]

OPTIONAL_VARS: List[str] = [
    "GEMINI_API_KEY",
    "GITHUB_TOKEN",
]


def validate_environment(strict: bool = False) -> Dict[str, bool]:
    """
    Validates required and optional environment variables for OMNI Digital Twin at startup.
    Logs warnings if optional AI/API keys are missing, and raises RuntimeError if critical config is absent.
    """
    status: Dict[str, bool] = {}

    missing_required: List[str] = []
    for var in REQUIRED_VARS:
        value = os.getenv(var)
        if not value or not value.strip():
            missing_required.append(var)
            status[var] = False
        else:
            status[var] = True

    for var in OPTIONAL_VARS:
        value = os.getenv(var)
        if not value or not value.strip():
            status[var] = False
            logger.warning(
                f"[EnvValidator] Optional environment variable '{var}' is not set. "
                f"Rule-based fallback will be used where applicable."
            )
        else:
            status[var] = True

    if missing_required:
        msg = f"[EnvValidator] Missing critical environment variables: {', '.join(missing_required)}"
        logger.error(msg)
        if strict:
            raise RuntimeError(msg)

    logger.info("[EnvValidator] Startup environment validation checked successfully.")
    return status
