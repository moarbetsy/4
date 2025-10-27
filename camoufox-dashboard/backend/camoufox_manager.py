import logging
import sys
from dataclasses import asdict
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import new utilities
from screen_utils import ScreenModeHandler, ScreenSize
from proxy_utils import parse_proxy_url, sanitize_proxy_for_logging
from crypto_utils import CryptoManager

# Import Camoufox directly from the cloned repository
sys.path.insert(0, '/workspace/project/camoufox/pythonlib')
try:
    from camoufox.async_api import AsyncCamoufox, AsyncNewBrowser
    from camoufox.utils import launch_options
    from browserforge.fingerprints import Screen
    CAMOUFOX_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Camoufox not available: {e}")
    CAMOUFOX_AVAILABLE = False

logger = logging.getLogger(__name__)

class CamoufoxManager:
    """Enhanced Camoufox browser management with advanced fingerprinting"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_configs: Dict[str, Dict[str, Any]] = {}
        
    async def create_browser_session(self, profile_id: str, config: Dict[str, Any], os_name: str) -> bool:
        """Create a new Camoufox browser session with advanced fingerprinting (legacy method)"""
        return await self.create_enhanced_browser_session(
            profile_id=profile_id,
            config=config,
            effective_os=os_name,
            screen_mode="random_session"
        )
    
    async def create_enhanced_browser_session(self, profile_id: str, config: Dict[str, Any], 
                                            effective_os: str, screen_mode: str = "random_session",
                                            fixed_screen: Optional[Dict[str, Any]] = None,
                                            distribution: Optional[List[Dict[str, Any]]] = None,
                                            proxy_url: Optional[str] = None) -> bool:
        """Create a new Camoufox browser session with enhanced screen and proxy support"""
        try:
            if not CAMOUFOX_AVAILABLE:
                logger.error("Camoufox is not available")
                return False
            
            # Select screen size based on profile configuration
            profile_data = {
                "screen_mode": screen_mode,
                "fixed_screen": fixed_screen,
                "distribution": distribution
            }
            selected_screen = ScreenModeHandler.select_screen_for_profile(profile_data)
            
            logger.info(f"Selected screen for profile {profile_id}: {selected_screen.screen_width}x{selected_screen.screen_height} (window: {selected_screen.window_width}x{selected_screen.window_height})")
            
            # Create Screen object for Camoufox
            screen_constraint = Screen(
                min_width=selected_screen.screen_width,
                max_width=selected_screen.screen_width,
                min_height=selected_screen.screen_height,
                max_height=selected_screen.screen_height
            )
            
            # Parse proxy configuration if provided
            proxy_config = None
            if proxy_url:
                try:
                    parsed_proxy = parse_proxy_url(proxy_url)
                    # Convert to Camoufox proxy format
                    proxy_config = {
                        "server": f"{parsed_proxy.protocol}://{parsed_proxy.host}:{parsed_proxy.port}"
                    }
                    if parsed_proxy.username and parsed_proxy.password:
                        proxy_config["username"] = parsed_proxy.username
                        proxy_config["password"] = parsed_proxy.password
                    
                    logger.info(f"Using proxy for profile {profile_id}: {sanitize_proxy_for_logging(proxy_url)}")
                except Exception as e:
                    logger.error(f"Failed to parse proxy URL for profile {profile_id}: {e}")
                    return False
            
            # Prepare Camoufox launch options
            base_config = config.copy()
            base_config.pop("effective_os", None)
            base_config.pop("screen_mode", None)
            base_config.pop("fixed_screen", None)
            base_config.pop("distribution", None)
            
            humanize_option = base_config.pop("humanize", True)
            headless_option = base_config.pop("headless", False)
            
            os_key = effective_os.lower() if effective_os else "windows"
            
            # Create launch options using Camoufox's launch_options function
            launch_opts = launch_options(
                config=base_config,
                os=os_key,
                screen=screen_constraint,
                window=(selected_screen.window_width, selected_screen.window_height),
                headless=headless_option,
                humanize=humanize_option,
                proxy=proxy_config,
                geoip=True if proxy_config else False,  # Enable geoip when using proxy
                i_know_what_im_doing=True
            )
            
            # Create Camoufox browser session
            browser_manager = AsyncCamoufox(**launch_opts)
            browser = await browser_manager.__aenter__()
            
            # Create a page
            page = await browser.new_page()
            context = page.context
            
            await page.bring_to_front()  # Ensure the new window is focused for user input
            
            session_config = {
                **base_config,
                "effective_os": effective_os,
                "screen_mode": screen_mode,
                "selected_screen": selected_screen.to_dict(),
                "humanize": humanize_option,
                "headless": headless_option,
                "has_proxy": proxy_config is not None,
                "proxy_host": f"{parsed_proxy.host}:{parsed_proxy.port}" if proxy_config and 'parsed_proxy' in locals() else None
            }
            
            # Store session information
            self.active_sessions[profile_id] = {
                "browser_manager": browser_manager,
                "browser": browser,
                "context": context,
                "page": page,
                "config": session_config,
                "created_at": datetime.now().isoformat(),
                "screen_config": selected_screen.to_dict()
            }
            
            self.session_configs[profile_id] = session_config
            
            logger.info(f"Enhanced browser session created for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating enhanced browser session for profile {profile_id}: {e}")
            return False
    
    async def close_browser_session(self, profile_id: str) -> bool:
        """Close a browser session"""
        try:
            if profile_id not in self.active_sessions:
                return False
                
            session = self.active_sessions[profile_id]
            browser_manager = session["browser_manager"]
            
            # Close the browser
            await browser_manager.__aexit__(None, None, None)
            
            # Remove from active sessions
            del self.active_sessions[profile_id]
            if profile_id in self.session_configs:
                del self.session_configs[profile_id]
            
            logger.info(f"Browser session closed for profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing browser session for profile {profile_id}: {e}")
            return False
    
    def get_session_info(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an active session"""
        if profile_id not in self.active_sessions:
            return None
            
        session = self.active_sessions[profile_id]
        return {
            "profile_id": profile_id,
            "created_at": session["created_at"],
            "uptime": (datetime.now() - datetime.fromisoformat(session["created_at"])).total_seconds(),
            "fingerprint_summary": self._get_fingerprint_summary(session["fingerprint"]),
            "config_summary": self._get_config_summary(session["config"]),
            "screen_config": session.get("screen_config", {}),
            "has_proxy": session["config"].get("has_proxy", False),
            "proxy_host": session["config"].get("proxy_host")
        }
    
    def is_session_active(self, profile_id: str) -> bool:
        """Check if a session is active"""
        return profile_id in self.active_sessions
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all active sessions"""
        sessions: Dict[str, Dict[str, Any]] = {}
        for profile_id in self.active_sessions:
            session_info = self.get_session_info(profile_id)
            if session_info is not None:
                sessions[profile_id] = session_info
        return sessions
    
    async def navigate_to_url(self, profile_id: str, url: str) -> bool:
        """Navigate to a URL in the specified profile's browser"""
        try:
            if profile_id not in self.active_sessions:
                return False
                
            session = self.active_sessions[profile_id]
            page = session["page"]
            
            await page.goto(url)
            logger.info(f"Navigated to {url} in profile {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to {url} in profile {profile_id}: {e}")
            return False
    
    def _get_geolocation_from_timezone(self, timezone: str) -> Dict[str, float]:
        """Get approximate geolocation based on timezone"""
        # Simplified mapping of timezones to approximate coordinates
        timezone_coords = {
            "GMT-12:00": {"latitude": -14.2710, "longitude": -170.1322},  # Baker Island
            "GMT-11:00": {"latitude": 21.3099, "longitude": -157.8581},   # Hawaii
            "GMT-10:00": {"latitude": 61.2181, "longitude": -149.9003},   # Alaska
            "GMT-09:00": {"latitude": 37.7749, "longitude": -122.4194},   # San Francisco
            "GMT-08:00": {"latitude": 34.0522, "longitude": -118.2437},   # Los Angeles
            "GMT-07:00": {"latitude": 39.7392, "longitude": -104.9903},   # Denver
            "GMT-06:00": {"latitude": 29.7604, "longitude": -95.3698},    # Houston
            "GMT-05:00": {"latitude": 40.7128, "longitude": -74.0060},    # New York
            "GMT-04:00": {"latitude": 25.7617, "longitude": -80.1918},    # Miami
            "GMT-03:00": {"latitude": -23.5505, "longitude": -46.6333},   # São Paulo
            "GMT-02:00": {"latitude": -22.9068, "longitude": -43.1729},   # Rio de Janeiro
            "GMT-01:00": {"latitude": 32.6612, "longitude": -16.9244},    # Madeira
            "GMT+00:00": {"latitude": 51.5074, "longitude": -0.1278},     # London
            "GMT+01:00": {"latitude": 52.5200, "longitude": 13.4050},     # Berlin
            "GMT+02:00": {"latitude": 59.3293, "longitude": 18.0686},     # Stockholm
            "GMT+03:00": {"latitude": 55.7558, "longitude": 37.6176},     # Moscow
            "GMT+04:00": {"latitude": 25.2048, "longitude": 55.2708},     # Dubai
            "GMT+05:00": {"latitude": 28.6139, "longitude": 77.2090},     # Delhi
            "GMT+06:00": {"latitude": 23.8103, "longitude": 90.4125},     # Dhaka
            "GMT+07:00": {"latitude": 13.7563, "longitude": 100.5018},    # Bangkok
            "GMT+08:00": {"latitude": 39.9042, "longitude": 116.4074},    # Beijing
            "GMT+09:00": {"latitude": 35.6762, "longitude": 139.6503},    # Tokyo
            "GMT+10:00": {"latitude": -33.8688, "longitude": 151.2093},   # Sydney
            "GMT+11:00": {"latitude": -37.8136, "longitude": 144.9631},   # Melbourne
            "GMT+12:00": {"latitude": -36.8485, "longitude": 174.7633},   # Auckland
        }
        
        return timezone_coords.get(timezone, {"latitude": 51.5074, "longitude": -0.1278})
    
    def _get_fingerprint_summary(self, fingerprint: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the fingerprint for display"""
        summary = {}
        
        if "navigator" in fingerprint:
            nav = fingerprint["navigator"]
            summary["user_agent"] = nav.get("userAgent", "Unknown")
            summary["platform"] = nav.get("platform", "Unknown")
            summary["language"] = nav.get("language", "Unknown")
        
        if "screen" in fingerprint:
            screen = fingerprint["screen"]
            summary["screen_resolution"] = f"{screen.get('width', 0)}x{screen.get('height', 0)}"
        
        return summary
    
    def _get_config_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the configuration for display"""
        summary = {
            "timezone": config.get("timezone", "Unknown"),
            "effective_os": config.get("effective_os", "Unknown"),
            "screen_mode": config.get("screen_mode", "random_session"),
            "humanize": config.get("humanize", False),
            "has_proxy": config.get("has_proxy", False),
            "addons_count": len(config.get("addons", [])),
            "fonts_count": len(config.get("fonts", []))
        }
        
        # Add screen information
        selected_screen = config.get("selected_screen")
        if selected_screen:
            summary["screen_resolution"] = f"{selected_screen.get('screen_width', 0)}x{selected_screen.get('screen_height', 0)}"
            summary["window_size"] = f"{selected_screen.get('window_width', 0)}x{selected_screen.get('window_height', 0)}"
        
        # Add proxy information (without credentials)
        if config.get("proxy_host"):
            summary["proxy_host"] = config["proxy_host"]
        
        return summary
