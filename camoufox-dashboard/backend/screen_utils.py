"""
Screen and window size utilities for profile screen mode handling.
"""
import random
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScreenSize:
    """Represents screen and window dimensions."""
    screen_width: int
    screen_height: int
    window_width: int
    window_height: int
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "weight": self.weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScreenSize':
        """Create from dictionary representation."""
        return cls(
            screen_width=data["screen_width"],
            screen_height=data["screen_height"],
            window_width=data["window_width"],
            window_height=data["window_height"],
            weight=data.get("weight", 1.0)
        )
    
    def validate(self) -> Dict[str, Any]:
        """Validate screen size parameters."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Basic validation
        if self.screen_width <= 0 or self.screen_height <= 0:
            result["valid"] = False
            result["errors"].append("Screen dimensions must be positive")
        
        if self.window_width <= 0 or self.window_height <= 0:
            result["valid"] = False
            result["errors"].append("Window dimensions must be positive")
        
        if self.weight <= 0:
            result["valid"] = False
            result["errors"].append("Weight must be positive")
        
        # Logical validation
        if self.window_width > self.screen_width:
            result["warnings"].append("Window width exceeds screen width")
        
        if self.window_height > self.screen_height:
            result["warnings"].append("Window height exceeds screen height")
        
        # Common resolution validation
        if self.screen_width < 800 or self.screen_height < 600:
            result["warnings"].append("Very small screen resolution may cause compatibility issues")
        
        if self.screen_width > 7680 or self.screen_height > 4320:  # 8K resolution
            result["warnings"].append("Very large screen resolution is uncommon and may be suspicious")
        
        # Window size recommendations
        if self.window_width < 400 or self.window_height < 300:
            result["warnings"].append("Very small window size may cause usability issues")
        
        return result

class ScreenModeHandler:
    """Handles different screen mode operations."""
    
    # Common screen resolutions with realistic distributions
    COMMON_RESOLUTIONS = [
        ScreenSize(1920, 1080, 1500, 900, weight=35.0),   # Full HD - most common
        ScreenSize(1366, 768, 1200, 700, weight=20.0),    # HD - laptops
        ScreenSize(1440, 900, 1300, 800, weight=12.0),    # MacBook Air
        ScreenSize(1536, 864, 1400, 750, weight=8.0),     # 1.5K
        ScreenSize(2560, 1440, 2000, 1200, weight=10.0),  # 2K
        ScreenSize(1280, 720, 1100, 650, weight=6.0),     # HD
        ScreenSize(1600, 900, 1400, 800, weight=4.0),     # HD+
        ScreenSize(3840, 2160, 2800, 1800, weight=3.0),   # 4K
        ScreenSize(1280, 1024, 1100, 900, weight=2.0),    # SXGA (older monitors)
    ]
    
    @staticmethod
    def get_random_screen() -> ScreenSize:
        """Get a random plausible screen size (existing behavior)."""
        return random.choices(
            ScreenModeHandler.COMMON_RESOLUTIONS,
            weights=[res.weight for res in ScreenModeHandler.COMMON_RESOLUTIONS]
        )[0]
    
    @staticmethod
    def sample_from_distribution(distribution: List[Dict[str, Any]]) -> ScreenSize:
        """Sample a screen size from a custom distribution."""
        if not distribution:
            logger.warning("Empty distribution provided, using random screen")
            return ScreenModeHandler.get_random_screen()
        
        try:
            # Convert to ScreenSize objects
            screen_sizes = [ScreenSize.from_dict(item) for item in distribution]
            weights = [size.weight for size in screen_sizes]
            
            # Validate weights
            if all(w <= 0 for w in weights):
                logger.warning("All weights are zero or negative, using equal weights")
                weights = [1.0] * len(weights)
            
            # Sample from distribution
            selected = random.choices(screen_sizes, weights=weights)[0]
            logger.info(f"Sampled screen size: {selected.screen_width}x{selected.screen_height}")
            return selected
            
        except Exception as e:
            logger.error(f"Error sampling from distribution: {e}")
            return ScreenModeHandler.get_random_screen()
    
    @staticmethod
    def select_screen_for_profile(profile_data: Dict[str, Any]) -> ScreenSize:
        """
        Select appropriate screen size based on profile screen mode.
        
        Args:
            profile_data: Profile configuration dictionary
            
        Returns:
            ScreenSize object for the session
        """
        screen_mode = profile_data.get("screen_mode", "random_session")
        
        if screen_mode == "fixed_profile":
            fixed_screen = profile_data.get("fixed_screen")
            if fixed_screen:
                try:
                    return ScreenSize.from_dict(fixed_screen)
                except Exception as e:
                    logger.error(f"Error parsing fixed screen config: {e}")
                    return ScreenModeHandler.get_random_screen()
            else:
                logger.warning("Fixed profile mode but no fixed_screen config, using random")
                return ScreenModeHandler.get_random_screen()
        
        elif screen_mode == "custom_distribution":
            distribution = profile_data.get("distribution", [])
            return ScreenModeHandler.sample_from_distribution(distribution)
        
        else:  # random_session or unknown
            return ScreenModeHandler.get_random_screen()
    
    @staticmethod
    def validate_screen_mode_config(screen_mode: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate screen mode configuration.
        
        Args:
            screen_mode: The screen mode ('random_session', 'fixed_profile', 'custom_distribution')
            config: Configuration data for the mode
            
        Returns:
            Validation result dictionary
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        valid_modes = ["random_session", "fixed_profile", "custom_distribution"]
        
        if screen_mode not in valid_modes:
            result["valid"] = False
            result["errors"].append(f"Invalid screen mode '{screen_mode}'. Must be one of: {', '.join(valid_modes)}")
            return result
        
        if screen_mode == "fixed_profile":
            fixed_screen = config.get("fixed_screen")
            if not fixed_screen:
                result["valid"] = False
                result["errors"].append("fixed_profile mode requires fixed_screen configuration")
            else:
                try:
                    screen_size = ScreenSize.from_dict(fixed_screen)
                    validation = screen_size.validate()
                    result["errors"].extend(validation["errors"])
                    result["warnings"].extend(validation["warnings"])
                    if not validation["valid"]:
                        result["valid"] = False
                except Exception as e:
                    result["valid"] = False
                    result["errors"].append(f"Invalid fixed_screen configuration: {e}")
        
        elif screen_mode == "custom_distribution":
            distribution = config.get("distribution", [])
            if not distribution:
                result["valid"] = False
                result["errors"].append("custom_distribution mode requires distribution configuration")
            else:
                try:
                    total_weight = 0
                    for i, item in enumerate(distribution):
                        screen_size = ScreenSize.from_dict(item)
                        validation = screen_size.validate()
                        
                        # Prefix errors/warnings with item index
                        for error in validation["errors"]:
                            result["errors"].append(f"Distribution item {i}: {error}")
                        for warning in validation["warnings"]:
                            result["warnings"].append(f"Distribution item {i}: {warning}")
                        
                        if not validation["valid"]:
                            result["valid"] = False
                        
                        total_weight += screen_size.weight
                    
                    if total_weight <= 0:
                        result["valid"] = False
                        result["errors"].append("Total weight of distribution must be positive")
                    
                except Exception as e:
                    result["valid"] = False
                    result["errors"].append(f"Invalid distribution configuration: {e}")
        
        return result

def get_default_screen_sizes() -> List[Dict[str, Any]]:
    """Get default screen size distribution for UI suggestions."""
    return [size.to_dict() for size in ScreenModeHandler.COMMON_RESOLUTIONS[:5]]  # Top 5 most common