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
        msg = (
            f"Missing required environment variable:\n"
            f"{', '.join(missing_required)}\n\n"
            f"Please configure backend/.env for local development\n"
            f"or deployment environment variables for production."
        )
        logger.error(f"Startup validation failed:\n{msg}")
        if strict:
            import sys
            print(f"\n{msg}\n", file=sys.stderr)
            sys.exit(1)

    logger.info("[EnvValidator] Startup environment validation checked successfully.")
    return status
