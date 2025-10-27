"""
Proxy utilities for parsing, validating, and handling proxy configurations.
"""
import re
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, ParseResult

logger = logging.getLogger(__name__)

class ProxyConfig:
    """Represents a parsed proxy configuration."""
    
    def __init__(self, protocol: str, host: str, port: int, 
                 username: Optional[str] = None, password: Optional[str] = None):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "protocol": self.protocol,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "has_auth": bool(self.username and self.password)
        }
    
    def to_url(self, include_auth: bool = True) -> str:
        """Convert back to URL format."""
        if include_auth and self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        else:
            return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_playwright_config(self) -> Dict[str, Any]:
        """Convert to Playwright proxy configuration format."""
        config = {
            "server": f"{self.protocol}://{self.host}:{self.port}"
        }
        
        if self.username and self.password:
            config["username"] = self.username
            config["password"] = self.password
        
        return config

def parse_proxy_url(proxy_url: str) -> ProxyConfig:
    """
    Parse a proxy URL into components.
    
    Supports formats:
    - http://host:port
    - https://host:port  
    - http://username:password@host:port
    - https://username:password@host:port
    
    Args:
        proxy_url: The proxy URL to parse
        
    Returns:
        ProxyConfig object
        
    Raises:
        ValueError: If the URL format is invalid
    """
    if not proxy_url or not isinstance(proxy_url, str):
        raise ValueError("Proxy URL must be a non-empty string")
    
    try:
        parsed: ParseResult = urlparse(proxy_url)
        
        # Validate protocol
        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"Unsupported proxy protocol '{parsed.scheme}'. Only http and https are supported.")
        
        # Validate host
        if not parsed.hostname:
            raise ValueError("Proxy URL must include a hostname")
        
        # Validate port
        if not parsed.port:
            raise ValueError("Proxy URL must include a port number")
        
        if not (1 <= parsed.port <= 65535):
            raise ValueError(f"Invalid port number {parsed.port}. Must be between 1 and 65535.")
        
        # Extract authentication if present
        username = parsed.username
        password = parsed.password
        
        # Validate authentication (both or neither)
        if (username is None) != (password is None):
            raise ValueError("Both username and password must be provided for authenticated proxies")
        
        return ProxyConfig(
            protocol=parsed.scheme,
            host=parsed.hostname,
            port=parsed.port,
            username=username,
            password=password
        )
        
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        else:
            raise ValueError(f"Invalid proxy URL format: {e}")

def validate_proxy_url(proxy_url: str) -> Dict[str, Any]:
    """
    Validate a proxy URL and return validation results.
    
    Args:
        proxy_url: The proxy URL to validate
        
    Returns:
        Dict with validation results, warnings, and parsed config
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "config": None
    }
    
    try:
        config = parse_proxy_url(proxy_url)
        result["valid"] = True
        result["config"] = config.to_dict()
        
        # Add warnings for common issues
        if config.protocol == "http":
            result["warnings"].append("HTTP proxy detected. Consider using HTTPS for better security.")
        
        if config.username and config.password:
            result["warnings"].append("Proxy credentials will be stored encrypted.")
        
        # Check for common problematic patterns
        if config.host in ["localhost", "127.0.0.1", "::1"]:
            result["warnings"].append("Localhost proxy detected. Ensure the proxy service is running.")
        
    except ValueError as e:
        result["errors"].append(str(e))
    except Exception as e:
        result["errors"].append(f"Unexpected error validating proxy: {e}")
    
    return result

def sanitize_proxy_for_logging(proxy_url: str) -> str:
    """
    Sanitize proxy URL for safe logging (removes credentials).
    
    Args:
        proxy_url: The proxy URL to sanitize
        
    Returns:
        Sanitized URL safe for logging
    """
    try:
        config = parse_proxy_url(proxy_url)
        return config.to_url(include_auth=False)
    except Exception:
        # If parsing fails, try basic regex replacement
        return re.sub(r'://[^@]+@', '://***:***@', proxy_url)

def test_proxy_connectivity(proxy_config: ProxyConfig, timeout: int = 10) -> Dict[str, Any]:
    """
    Test basic connectivity to a proxy server.
    
    Args:
        proxy_config: The proxy configuration to test
        timeout: Connection timeout in seconds
        
    Returns:
        Dict with test results
    """
    import socket
    
    result = {
        "reachable": False,
        "error": None,
        "response_time_ms": None
    }
    
    try:
        import time
        start_time = time.time()
        
        # Test basic TCP connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        connection_result = sock.connect_ex((proxy_config.host, proxy_config.port))
        sock.close()
        
        end_time = time.time()
        result["response_time_ms"] = int((end_time - start_time) * 1000)
        
        if connection_result == 0:
            result["reachable"] = True
        else:
            result["error"] = f"Connection failed with code {connection_result}"
            
    except socket.timeout:
        result["error"] = f"Connection timeout after {timeout} seconds"
    except Exception as e:
        result["error"] = f"Connection test failed: {e}"
    
    return result