"""
Operating system detection utilities for automatic OS fingerprinting.
"""
import platform
import sys
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def detect_host_os() -> str:
    """
    Detect the host operating system and return a normalized OS string.
    
    Returns:
        str: One of 'windows', 'macos', 'linux'
    """
    system = platform.system().lower()
    
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        # Default to linux for unknown systems
        logger.warning(f"Unknown OS detected: {system}, defaulting to linux")
        return "linux"

def get_host_os_details() -> Dict[str, Any]:
    """
    Get detailed information about the host operating system.
    
    Returns:
        Dict containing OS details for fingerprinting
    """
    try:
        return {
            "os": detect_host_os(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "architecture": platform.architecture()[0]
        }
    except Exception as e:
        logger.error(f"Error getting OS details: {e}")
        return {
            "os": detect_host_os(),
            "platform": "unknown",
            "system": "unknown",
            "release": "unknown",
            "version": "unknown",
            "machine": "unknown",
            "processor": "unknown",
            "python_version": sys.version,
            "architecture": "unknown"
        }

def validate_os_override(os_override: str, host_os: str) -> Dict[str, Any]:
    """
    Validate OS override and return warnings if there are potential issues.
    
    Args:
        os_override: The OS the user wants to override to
        host_os: The actual host OS
    
    Returns:
        Dict with validation result and warnings
    """
    valid_os_values = ["windows", "macos", "linux"]
    
    result = {
        "valid": True,
        "warnings": [],
        "normalized_os": os_override.lower()
    }
    
    # Validate OS value
    if os_override.lower() not in valid_os_values:
        result["valid"] = False
        result["warnings"].append(f"Invalid OS value '{os_override}'. Must be one of: {', '.join(valid_os_values)}")
        return result
    
    # Check for OS mismatch warnings
    if os_override.lower() != host_os.lower():
        result["warnings"].extend([
            f"OS override '{os_override}' differs from host OS '{host_os}'",
            "This may cause fingerprint mismatches and site breakage",
            "Browser fonts, GPU info, and platform APIs may not match the spoofed OS",
            "Consider using host OS for better compatibility"
        ])
    
    return result