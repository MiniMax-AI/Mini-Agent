"""Fix for ACP schema to handle clients sending protocolVersion as string.

Some ACP clients (like Zed) incorrectly send protocolVersion as "1.0.0"
instead of an integer as specified in the ACP spec. This module patches
the ACP library to handle both formats gracefully.
"""
import logging
from typing import Any

from pydantic import field_validator

import acp.schema

logger = logging.getLogger(__name__)


# Save reference to original InitializeRequest class
_original_init_request = acp.schema.InitializeRequest


class FixedInitializeRequest(_original_init_request):
    """Fixed InitializeRequest that accepts string protocolVersion from non-compliant clients.

    ACP spec requires protocolVersion to be an integer (uint16), but some clients
    send it as a string like "1.0.0". This class handles both formats.
    """

    @field_validator('protocolVersion', mode='before')
    @classmethod
    def convert_protocol_version(cls, v: Any) -> int:
        """Convert protocolVersion to int, handling string formats.

        Args:
            v: The protocolVersion value (int or string)

        Returns:
            Integer protocol version

        Examples:
            - "1.0.0" -> 1
            - "2" -> 2
            - 1 -> 1
        """
        if isinstance(v, str):
            # Handle version strings like "1.0.0", "2.1", etc.
            # Extract the major version number
            try:
                # Split on '.' and take first part
                major_version = v.split('.')[0]
                result = int(major_version)
                logger.debug(f"Converted string protocolVersion '{v}' to int {result}")
                return result
            except (ValueError, IndexError, AttributeError) as e:
                logger.warning(f"Failed to parse protocolVersion '{v}': {e}. Defaulting to 1")
                return 1  # Default to version 1
        elif isinstance(v, (int, float)):
            # Already numeric, just convert to int
            return int(v)
        else:
            logger.warning(f"Unexpected protocolVersion type {type(v)}: {v}. Defaulting to 1")
            return 1


# Rebuild the pydantic model to apply our validator
# This is CRITICAL because Pydantic v2 compiles validators at class creation time
try:
    FixedInitializeRequest.model_rebuild(force=True)
    logger.debug("Rebuilt FixedInitializeRequest pydantic model")
except Exception as e:
    logger.warning(f"Could not rebuild pydantic model: {e}")

# Replace the original class with our fixed version
acp.schema.InitializeRequest = FixedInitializeRequest
logger.info("Applied InitializeRequest monkeypatch for protocolVersion compatibility")


def apply_fixes():
    """Apply all ACP schema fixes.

    This function is called by server.py to ensure all fixes are applied.
    The monkeypatch is actually applied on module import, so this is a no-op.
    """
    pass
