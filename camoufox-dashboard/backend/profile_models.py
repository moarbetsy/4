"""
Enhanced profile models with screen modes, proxy support, and OS detection.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import logging

from proxy_utils import validate_proxy_url, sanitize_proxy_for_logging
from screen_utils import ScreenModeHandler
from os_detection import detect_host_os, validate_os_override

logger = logging.getLogger(__name__)

class ScreenSize(BaseModel):
    """Screen and window size configuration."""
    screen_width: int = Field(..., ge=1, le=10000, description="Screen width in pixels")
    screen_height: int = Field(..., ge=1, le=10000, description="Screen height in pixels") 
    window_width: int = Field(..., ge=1, le=10000, description="Window width in pixels")
    window_height: int = Field(..., ge=1, le=10000, description="Window height in pixels")
    weight: float = Field(1.0, gt=0, description="Weight for distribution sampling")

class DistributionItem(BaseModel):
    """Single item in a custom screen distribution."""
    screen_width: int = Field(..., ge=1, le=10000)
    screen_height: int = Field(..., ge=1, le=10000)
    window_width: int = Field(..., ge=1, le=10000)
    window_height: int = Field(..., ge=1, le=10000)
    weight: float = Field(..., gt=0)

class ProfileCreateRequest(BaseModel):
    """Request model for creating a new profile."""
    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    
    # Screen configuration
    screen_mode: str = Field("random_session", description="Screen mode: random_session, fixed_profile, or custom_distribution")
    fixed_screen: Optional[ScreenSize] = Field(None, description="Fixed screen size (required for fixed_profile mode)")
    distribution: Optional[List[DistributionItem]] = Field(None, description="Screen distribution (required for custom_distribution mode)")
    
    # Proxy configuration
    proxy: Optional[str] = Field(None, description="Proxy URL in format protocol://[user:pass@]host:port")
    
    # OS configuration
    use_host_os: bool = Field(True, description="Use the host OS for fingerprinting (recommended)")
    os_override: Optional[str] = Field(None, description="Override OS (not recommended)")
    
    # Legacy fields for backward compatibility
    timezone: str = Field("GMT+00:00", description="Timezone for geolocation")
    
    @field_validator('screen_mode')
    @classmethod
    def validate_screen_mode(cls, v):
        valid_modes = ["random_session", "fixed_profile", "custom_distribution"]
        if v not in valid_modes:
            raise ValueError(f"screen_mode must be one of: {', '.join(valid_modes)}")
        return v
    
    @field_validator('proxy')
    @classmethod
    def validate_proxy(cls, v):
        if v is not None:
            validation = validate_proxy_url(v)
            if not validation["valid"]:
                raise ValueError(f"Invalid proxy URL: {'; '.join(validation['errors'])}")
        return v
    
    @field_validator('os_override')
    @classmethod
    def validate_os_override(cls, v):
        if v is not None:
            valid_os = ["windows", "macos", "linux"]
            if v.lower() not in valid_os:
                raise ValueError(f"os_override must be one of: {', '.join(valid_os)}")
        return v.lower() if v else None
    
    @model_validator(mode='after')
    def validate_screen_config(self):
        screen_mode = self.screen_mode
        fixed_screen = self.fixed_screen
        distribution = self.distribution
        
        if screen_mode == "fixed_profile":
            if not fixed_screen:
                raise ValueError("fixed_profile mode requires fixed_screen configuration")
        elif screen_mode == "custom_distribution":
            if not distribution or len(distribution) == 0:
                raise ValueError("custom_distribution mode requires distribution configuration")
            
            # Validate total weight
            total_weight = sum(item.weight for item in distribution)
            if total_weight <= 0:
                raise ValueError("Total weight of distribution must be positive")
        
        return self
    
    @model_validator(mode='after')
    def validate_os_config(self):
        use_host_os = self.use_host_os
        os_override = self.os_override
        
        if not use_host_os and not os_override:
            raise ValueError("os_override is required when use_host_os is False")
        
        return self

class Profile(BaseModel):
    """Complete profile model with all configuration."""
    id: str
    name: str
    
    # Screen configuration
    screen_mode: str = "random_session"
    fixed_screen: Optional[Dict[str, Any]] = None
    distribution: Optional[List[Dict[str, Any]]] = None
    
    # Proxy configuration (stored encrypted)
    proxy_encrypted: Optional[str] = Field(None, description="Encrypted proxy configuration")
    has_proxy: bool = Field(False, description="Whether profile has proxy configured")
    
    # OS configuration
    use_host_os: bool = True
    os_override: Optional[str] = None
    effective_os: str = Field(..., description="The OS that will be used for fingerprinting")
    
    # Legacy fields
    timezone: str = "GMT+00:00"
    
    # Metadata
    status: str = "inactive"
    created_at: str
    config: Optional[Dict[str, Any]] = None
    
    # Warnings for user
    warnings: List[str] = Field(default_factory=list, description="Configuration warnings")

class ProfileResponse(BaseModel):
    """Response model for profile operations (excludes sensitive data)."""
    id: str
    name: str
    screen_mode: str
    fixed_screen: Optional[Dict[str, Any]] = None
    distribution: Optional[List[Dict[str, Any]]] = None
    has_proxy: bool = False
    proxy_host: Optional[str] = Field(None, description="Proxy host (for display only)")
    use_host_os: bool = True
    os_override: Optional[str] = None
    effective_os: str
    timezone: str
    status: str
    created_at: str
    warnings: List[str] = Field(default_factory=list)
    
    @classmethod
    def from_profile(cls, profile: Profile, proxy_url: Optional[str] = None) -> 'ProfileResponse':
        """Create response model from full profile, optionally including proxy info."""
        proxy_host = None
        if proxy_url:
            try:
                from proxy_utils import parse_proxy_url
                proxy_config = parse_proxy_url(proxy_url)
                proxy_host = f"{proxy_config.host}:{proxy_config.port}"
            except Exception:
                proxy_host = "configured"
        
        return cls(
            id=profile.id,
            name=profile.name,
            screen_mode=profile.screen_mode,
            fixed_screen=profile.fixed_screen,
            distribution=profile.distribution,
            has_proxy=profile.has_proxy,
            proxy_host=proxy_host,
            use_host_os=profile.use_host_os,
            os_override=profile.os_override,
            effective_os=profile.effective_os,
            timezone=profile.timezone,
            status=profile.status,
            created_at=profile.created_at,
            warnings=profile.warnings
        )

class ProfileValidationResult(BaseModel):
    """Result of profile validation."""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    effective_os: Optional[str] = None

def validate_profile_create_request(request: ProfileCreateRequest) -> ProfileValidationResult:
    """
    Comprehensive validation of profile creation request.
    
    Args:
        request: The profile creation request to validate
        
    Returns:
        ProfileValidationResult with validation details
    """
    result = ProfileValidationResult(valid=True)
    
    # Determine effective OS
    host_os = detect_host_os()
    if request.use_host_os:
        effective_os = host_os
    else:
        effective_os = request.os_override or host_os
        
        # Add OS override warnings
        if request.os_override:
            os_validation = validate_os_override(request.os_override, host_os)
            result.warnings.extend(os_validation["warnings"])
    
    result.effective_os = effective_os
    
    # Validate screen configuration
    screen_config = {
        "fixed_screen": request.fixed_screen.dict() if request.fixed_screen else None,
        "distribution": [item.dict() for item in request.distribution] if request.distribution else None
    }
    
    screen_validation = ScreenModeHandler.validate_screen_mode_config(
        request.screen_mode, screen_config
    )
    
    result.errors.extend(screen_validation["errors"])
    result.warnings.extend(screen_validation["warnings"])
    
    if not screen_validation["valid"]:
        result.valid = False
    
    # Validate proxy if provided
    if request.proxy:
        proxy_validation = validate_proxy_url(request.proxy)
        result.errors.extend(proxy_validation["errors"])
        result.warnings.extend(proxy_validation["warnings"])
        
        if not proxy_validation["valid"]:
            result.valid = False
    
    return result