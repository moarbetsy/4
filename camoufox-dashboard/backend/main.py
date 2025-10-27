from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import uuid
import asyncio
from datetime import datetime
import logging
from camoufox_manager import CamoufoxManager

# Import new modules
from profile_models import (
    ProfileCreateRequest, Profile, ProfileResponse, 
    validate_profile_create_request
)
from crypto_utils import (
    encrypt_sensitive_data, decrypt_sensitive_data, 
    is_encryption_available
)
from os_detection import detect_host_os
from proxy_utils import sanitize_proxy_for_logging
from screen_utils import get_default_screen_sizes

# Ensure Windows event loop supports subprocesses (required by Playwright).
if os.name == "nt":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        logging.getLogger(__name__).warning(
            "WindowsProactorEventLoopPolicy unavailable; Playwright may fail to launch."
        )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Camoufox Dashboard API", version="1.0.0")

# Legacy data models for backward compatibility
class ProfileCreate(BaseModel):
    """Legacy profile creation model - deprecated, use ProfileCreateRequest instead."""
    name: str
    os: str
    timezone: str

class ProfileManager:
    def __init__(self):
        self.profiles_file = "profiles.json"
        self.camoufox_manager = CamoufoxManager()  # Enhanced Camoufox manager
        self.host_os = detect_host_os()
        
        # Check encryption availability
        if not is_encryption_available():
            logger.error("Encryption not available! Proxy credentials cannot be stored securely.")
            raise RuntimeError("Encryption initialization failed. Cannot store sensitive data securely.")
        
        self.load_profiles()

    def load_profiles(self):
        """Load profiles from JSON file with migration support"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    self.profiles = []
                    
                    for profile_data in data:
                        try:
                            # Migrate legacy profiles to new schema
                            migrated_profile = self._migrate_legacy_profile(profile_data)
                            profile = Profile(**migrated_profile)
                            self.profiles.append(profile)
                        except Exception as e:
                            logger.error(f"Error loading profile {profile_data.get('id', 'unknown')}: {e}")
                            continue
            else:
                self.profiles = []
                
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            self.profiles = []

    def _migrate_legacy_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate legacy profile format to new schema"""
        # If already new format, return as-is
        if "screen_mode" in profile_data:
            return profile_data
        
        # Migrate legacy format
        migrated = {
            "id": profile_data.get("id", str(uuid.uuid4())),
            "name": profile_data.get("name", "Migrated Profile"),
            "screen_mode": "random_session",  # Default for legacy profiles
            "fixed_screen": None,
            "distribution": None,
            "proxy_encrypted": None,
            "has_proxy": False,
            "use_host_os": True,
            "os_override": None,
            "effective_os": self.host_os,  # Use current host OS
            "timezone": profile_data.get("timezone", "GMT+00:00"),
            "status": profile_data.get("status", "inactive"),
            "created_at": profile_data.get("created_at", datetime.now().isoformat()),
            "config": profile_data.get("config"),
            "warnings": []
        }
        
        # If legacy profile had OS specified, add warning about migration
        legacy_os = profile_data.get("os")
        if legacy_os and legacy_os.lower() != self.host_os.lower():
            migrated["warnings"].append(f"Profile migrated from legacy OS '{legacy_os}' to host OS '{self.host_os}'")
        
        logger.info(f"Migrated legacy profile: {migrated['name']}")
        return migrated

    def save_profiles(self):
        """Save profiles to JSON file"""
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump([profile.dict() for profile in self.profiles], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")

    def create_profile(self, profile_data: ProfileCreate) -> Profile:
        """Create a new profile (legacy method for backward compatibility)"""
        # Convert legacy request to new format
        new_request = ProfileCreateRequest(
            name=profile_data.name,
            screen_mode="random_session",
            use_host_os=True,
            timezone=profile_data.timezone
        )
        return self.create_enhanced_profile(new_request)
    
    def create_enhanced_profile(self, request: ProfileCreateRequest) -> Profile:
        """Create a new profile with enhanced features"""
        # Validate the request
        validation = validate_profile_create_request(request)
        if not validation.valid:
            raise ValueError(f"Profile validation failed: {'; '.join(validation.errors)}")
        
        profile_id = str(uuid.uuid4())
        
        # Handle proxy encryption
        proxy_encrypted = None
        has_proxy = False
        if request.proxy:
            try:
                proxy_encrypted = encrypt_sensitive_data(request.proxy)
                has_proxy = True
                logger.info(f"Proxy configured for profile {request.name}: {sanitize_proxy_for_logging(request.proxy)}")
            except Exception as e:
                logger.error(f"Failed to encrypt proxy for profile {request.name}: {e}")
                raise ValueError("Failed to securely store proxy credentials")
        
        # Generate Camoufox configuration
        config = self.generate_enhanced_camoufox_config(
            effective_os=validation.effective_os,
            timezone=request.timezone,
            screen_mode=request.screen_mode,
            fixed_screen=request.fixed_screen.dict() if request.fixed_screen else None,
            distribution=[item.dict() for item in request.distribution] if request.distribution else None
        )
        
        profile = Profile(
            id=profile_id,
            name=request.name,
            screen_mode=request.screen_mode,
            fixed_screen=request.fixed_screen.dict() if request.fixed_screen else None,
            distribution=[item.dict() for item in request.distribution] if request.distribution else None,
            proxy_encrypted=proxy_encrypted,
            has_proxy=has_proxy,
            use_host_os=request.use_host_os,
            os_override=request.os_override,
            effective_os=validation.effective_os,
            timezone=request.timezone,
            status="inactive",
            created_at=datetime.now().isoformat(),
            config=config,
            warnings=validation.warnings
        )
        
        self.profiles.append(profile)
        self.save_profiles()
        
        logger.info(f"Created enhanced profile: {profile.name} (ID: {profile_id})")
        if validation.warnings:
            logger.warning(f"Profile {profile.name} has warnings: {'; '.join(validation.warnings)}")
        
        return profile

    def get_profiles(self) -> List[Profile]:
        """Get all profiles"""
        return self.profiles

    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get a specific profile by ID"""
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None
    
    def get_profile_proxy(self, profile: Profile) -> Optional[str]:
        """Get decrypted proxy URL for a profile"""
        if not profile.has_proxy or not profile.proxy_encrypted:
            return None
        
        try:
            return decrypt_sensitive_data(profile.proxy_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt proxy for profile {profile.id}: {e}")
            return None

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile"""
        # Stop browser if active
        if self.camoufox_manager.is_session_active(profile_id):
            asyncio.create_task(self.camoufox_manager.close_browser_session(profile_id))
        
        # Remove from profiles list
        self.profiles = [p for p in self.profiles if p.id != profile_id]
        self.save_profiles()
        return True

    def generate_camoufox_config(self, os: str, timezone: str) -> Dict[str, Any]:
        """Generate baseline Camoufox configuration based on OS and timezone (legacy)."""
        return self.generate_enhanced_camoufox_config(
            effective_os=os,
            timezone=timezone,
            screen_mode="random_session"
        )
    
    def generate_enhanced_camoufox_config(self, effective_os: str, timezone: str, 
                                        screen_mode: str, fixed_screen: Optional[Dict[str, Any]] = None,
                                        distribution: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate enhanced Camoufox configuration with screen and proxy support."""
        config = {
            "effective_os": effective_os,
            "timezone": timezone,
            "locale:language": "en",
            "locale:region": "US",
            "humanize": True,
            "showcursor": True,
            "headless": False,
            "screen_mode": screen_mode,
        }
        
        # Add screen configuration
        if screen_mode == "fixed_profile" and fixed_screen:
            config["fixed_screen"] = fixed_screen
        elif screen_mode == "custom_distribution" and distribution:
            config["distribution"] = distribution
        
        return config

    async def launch_browser(self, profile_id: str) -> bool:
        """Launch a browser instance for the profile"""
        try:
            profile = self.get_profile(profile_id)
            if not profile:
                return False

            # Get proxy configuration if available
            proxy_url = self.get_profile_proxy(profile)

            # Ensure we always pass a concrete config to the manager
            config = profile.config or self.generate_enhanced_camoufox_config(
                effective_os=profile.effective_os,
                timezone=profile.timezone,
                screen_mode=profile.screen_mode,
                fixed_screen=profile.fixed_screen,
                distribution=profile.distribution
            )
            config["showcursor"] = True
            config["headless"] = False
            profile.config = config

            # Use the enhanced Camoufox manager with new parameters
            success = await self.camoufox_manager.create_enhanced_browser_session(
                profile_id=profile_id,
                config=config,
                effective_os=profile.effective_os,
                screen_mode=profile.screen_mode,
                fixed_screen=profile.fixed_screen,
                distribution=profile.distribution,
                proxy_url=proxy_url
            )
            
            if success:
                # Update profile status
                profile.status = "active"
                self.save_profiles()
                logger.info(f"Browser launched for profile {profile.name} ({profile_id})")
                if proxy_url:
                    logger.info(f"Profile {profile.name} using proxy: {sanitize_proxy_for_logging(proxy_url)}")
            
            return success

        except Exception as e:
            logger.error(f"Error launching browser for profile {profile_id}: {e}")
            return False

    async def stop_browser(self, profile_id: str) -> bool:
        """Stop a browser instance"""
        try:
            success = await self.camoufox_manager.close_browser_session(profile_id)
            
            if success:
                # Update profile status
                profile = self.get_profile(profile_id)
                if profile:
                    profile.status = "inactive"
                    self.save_profiles()
                logger.info(f"Browser stopped for profile {profile_id}")
            
            return success

        except Exception as e:
            logger.error(f"Error stopping browser for profile {profile_id}: {e}")
            return False

# Initialize profile manager
profile_manager = ProfileManager()

# API Routes
@app.get("/api/profiles", response_model=List[ProfileResponse])
async def get_profiles():
    """Get all profiles"""
    profiles = profile_manager.get_profiles()
    return [ProfileResponse.from_profile(profile) for profile in profiles]

@app.post("/api/profiles", response_model=ProfileResponse)
async def create_profile(profile_data: ProfileCreate):
    """Create a new profile (legacy endpoint)"""
    try:
        profile = profile_manager.create_profile(profile_data)
        return ProfileResponse.from_profile(profile)
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profiles/enhanced", response_model=ProfileResponse)
async def create_enhanced_profile(request: ProfileCreateRequest):
    """Create a new profile with enhanced features"""
    try:
        profile = profile_manager.create_enhanced_profile(request)
        proxy_url = profile_manager.get_profile_proxy(profile) if profile.has_proxy else None
        return ProfileResponse.from_profile(profile, proxy_url)
    except Exception as e:
        logger.error(f"Error creating enhanced profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str):
    """Get a specific profile"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    proxy_url = profile_manager.get_profile_proxy(profile) if profile.has_proxy else None
    return ProfileResponse.from_profile(profile, proxy_url)

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    success = profile_manager.delete_profile(profile_id)
    if success:
        return {"message": "Profile deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete profile")

@app.post("/api/profiles/{profile_id}/launch")
async def launch_profile(profile_id: str, background_tasks: BackgroundTasks):
    """Launch a browser instance for the profile"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if profile_manager.camoufox_manager.is_session_active(profile_id):
        raise HTTPException(status_code=400, detail="Profile is already active")
    
    # Launch browser in background
    background_tasks.add_task(profile_manager.launch_browser, profile_id)
    
    return {"message": "Browser launch initiated"}

@app.post("/api/profiles/{profile_id}/stop")
async def stop_profile(profile_id: str, background_tasks: BackgroundTasks):
    """Stop a browser instance for the profile"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not profile_manager.camoufox_manager.is_session_active(profile_id):
        raise HTTPException(status_code=400, detail="Profile is not active")
    
    # Stop browser in background
    background_tasks.add_task(profile_manager.stop_browser, profile_id)
    
    return {"message": "Browser stop initiated"}

@app.get("/api/profiles/{profile_id}/status")
async def get_profile_status(profile_id: str):
    """Get the current status of a profile"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    session_info = profile_manager.camoufox_manager.get_session_info(profile_id)
    
    return {
        "profile_id": profile_id,
        "status": "active" if session_info else "inactive",
        "session_info": session_info
    }

@app.post("/api/profiles/{profile_id}/test")
async def test_profile_browser(profile_id: str):
    """Test if the browser is working by navigating to a URL"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not profile_manager.camoufox_manager.is_session_active(profile_id):
        raise HTTPException(status_code=400, detail="Profile is not active")
    
    try:
        # Navigate to a test URL
        success = await profile_manager.camoufox_manager.navigate_to_url(profile_id, "https://httpbin.org/user-agent")
        if success:
            return {"message": "Browser test successful - navigated to test URL"}
        else:
            return {"message": "Browser test failed - could not navigate"}
    except Exception as e:
        logger.error(f"Browser test error: {e}")
        raise HTTPException(status_code=500, detail=f"Browser test failed: {str(e)}")

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file"""
    return FileResponse("../frontend/index.html")

@app.get("/app.js")
async def serve_js():
    """Serve the JavaScript file"""
    return FileResponse("../frontend/app.js")

# Utility endpoints
@app.get("/api/screen-sizes")
async def get_default_screen_sizes():
    """Get default screen size suggestions"""
    return {
        "common_sizes": get_default_screen_sizes(),
        "description": "Common screen resolutions with realistic usage weights"
    }

@app.get("/api/host-info")
async def get_host_info():
    """Get host system information"""
    from os_detection import get_host_os_details
    return get_host_os_details()

@app.post("/api/validate-proxy")
async def validate_proxy_endpoint(proxy_data: dict):
    """Validate a proxy URL"""
    proxy_url = proxy_data.get("proxy")
    if not proxy_url:
        raise HTTPException(status_code=400, detail="proxy field is required")
    
    from proxy_utils import validate_proxy_url
    validation = validate_proxy_url(proxy_url)
    
    return {
        "valid": validation["valid"],
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "sanitized_url": sanitize_proxy_for_logging(proxy_url) if validation["valid"] else None
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    active_sessions = profile_manager.camoufox_manager.get_active_sessions()
    return {
        "status": "healthy",
        "active_browsers": len(active_sessions),
        "total_profiles": len(profile_manager.profiles),
        "active_sessions": active_sessions,
        "host_os": profile_manager.host_os,
        "encryption_available": is_encryption_available()
    }

# Additional API endpoints for enhanced functionality
@app.post("/api/profiles/{profile_id}/navigate")
async def navigate_profile(profile_id: str, url: str):
    """Navigate to a URL in the specified profile's browser"""
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if not profile_manager.camoufox_manager.is_session_active(profile_id):
        raise HTTPException(status_code=400, detail="Profile is not active")
    
    success = await profile_manager.camoufox_manager.navigate_to_url(profile_id, url)
    if success:
        return {"message": f"Navigated to {url}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to navigate")

@app.get("/api/sessions")
async def get_active_sessions():
    """Get all active browser sessions"""
    return profile_manager.camoufox_manager.get_active_sessions()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12000)
