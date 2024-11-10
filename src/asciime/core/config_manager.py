"""
ASCIIme configuration manager - Handles loading and saving of user configuration.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConfigDefaults:
    """Default configuration values and constraints."""
    DISPLAY_MODES = ["truecolor", "256", "256fgbg", "nocolor"]
    DEFAULT_DISPLAY_MODE = "truecolor"
    MIN_CACHE_SIZE = 10
    MAX_CACHE_SIZE = 1000
    DEFAULT_CACHE_SIZE = 100
    MIN_CACHE_AGE = 1
    MAX_CACHE_AGE = 90
    DEFAULT_CACHE_AGE = 30
    MIN_PREFETCH = 1
    MAX_PREFETCH = 10
    DEFAULT_PREFETCH = 3
    DEFAULT_API_URL = "https://asciime-api.onrender.com/api"
    MIN_LOOP_COUNT = 0
    MAX_LOOP_COUNT = 100
    DEFAULT_LOOP_COUNT = 1

DEFAULT_CONFIG = {
    "display_mode": ConfigDefaults.DEFAULT_DISPLAY_MODE,
    "max_cache_size_mb": ConfigDefaults.DEFAULT_CACHE_SIZE,
    "max_cache_age_days": ConfigDefaults.DEFAULT_CACHE_AGE,
    "prefetch_count": ConfigDefaults.DEFAULT_PREFETCH,
    "api_url": ConfigDefaults.DEFAULT_API_URL,
    "preferred_category": None,
    "loop_count": ConfigDefaults.DEFAULT_LOOP_COUNT,
    "debug": False
}

class ConfigError(Exception):
    """Base class for configuration-related errors."""
    pass

class ConfigValidationError(ConfigError):
    """Raised when configuration validation fails."""
    pass

class ConfigManager:
    """Manages ASCIIme configuration loading, saving, and validation."""
    
    def __init__(self, config_dir: str = "~/.config/asciime"):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory path for configuration files
        """
        self.config_dir = os.path.expanduser(config_dir)
        self.config_file = os.path.join(self.config_dir, "config.json")
        self._ensure_config()

    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize configuration values.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Validated and normalized configuration dictionary
            
        Raises:
            ConfigValidationError: If validation fails
        """
        validated = {}
        
        # Display mode
        display_mode = config.get("display_mode", ConfigDefaults.DEFAULT_DISPLAY_MODE)
        if display_mode not in ConfigDefaults.DISPLAY_MODES:
            logger.warning(
                f"Invalid display_mode '{display_mode}', "
                f"using default: {ConfigDefaults.DEFAULT_DISPLAY_MODE}"
            )
            display_mode = ConfigDefaults.DEFAULT_DISPLAY_MODE
        validated["display_mode"] = display_mode
        
        # Cache size
        cache_size = config.get("max_cache_size_mb", ConfigDefaults.DEFAULT_CACHE_SIZE)
        try:
            cache_size = int(cache_size)
            if not ConfigDefaults.MIN_CACHE_SIZE <= cache_size <= ConfigDefaults.MAX_CACHE_SIZE:
                logger.warning(
                    f"Cache size {cache_size}MB out of range "
                    f"({ConfigDefaults.MIN_CACHE_SIZE}-{ConfigDefaults.MAX_CACHE_SIZE}MB), "
                    f"using default: {ConfigDefaults.DEFAULT_CACHE_SIZE}MB"
                )
                cache_size = ConfigDefaults.DEFAULT_CACHE_SIZE
        except (TypeError, ValueError):
            logger.warning(f"Invalid cache size, using default: {ConfigDefaults.DEFAULT_CACHE_SIZE}MB")
            cache_size = ConfigDefaults.DEFAULT_CACHE_SIZE
        validated["max_cache_size_mb"] = cache_size
        
        # Cache age
        cache_age = config.get("max_cache_age_days", ConfigDefaults.DEFAULT_CACHE_AGE)
        try:
            cache_age = int(cache_age)
            if not ConfigDefaults.MIN_CACHE_AGE <= cache_age <= ConfigDefaults.MAX_CACHE_AGE:
                logger.warning(
                    f"Cache age {cache_age} days out of range "
                    f"({ConfigDefaults.MIN_CACHE_AGE}-{ConfigDefaults.MAX_CACHE_AGE} days), "
                    f"using default: {ConfigDefaults.DEFAULT_CACHE_AGE} days"
                )
                cache_age = ConfigDefaults.DEFAULT_CACHE_AGE
        except (TypeError, ValueError):
            logger.warning(f"Invalid cache age, using default: {ConfigDefaults.DEFAULT_CACHE_AGE} days")
            cache_age = ConfigDefaults.DEFAULT_CACHE_AGE
        validated["max_cache_age_days"] = cache_age
        
        # Prefetch count
        prefetch = config.get("prefetch_count", ConfigDefaults.DEFAULT_PREFETCH)
        try:
            prefetch = int(prefetch)
            if not ConfigDefaults.MIN_PREFETCH <= prefetch <= ConfigDefaults.MAX_PREFETCH:
                logger.warning(
                    f"Prefetch count {prefetch} out of range "
                    f"({ConfigDefaults.MIN_PREFETCH}-{ConfigDefaults.MAX_PREFETCH}), "
                    f"using default: {ConfigDefaults.DEFAULT_PREFETCH}"
                )
                prefetch = ConfigDefaults.DEFAULT_PREFETCH
        except (TypeError, ValueError):
            logger.warning(f"Invalid prefetch count, using default: {ConfigDefaults.DEFAULT_PREFETCH}")
            prefetch = ConfigDefaults.DEFAULT_PREFETCH
        validated["prefetch_count"] = prefetch
        
        # API URL
        api_url = config.get("api_url", ConfigDefaults.DEFAULT_API_URL)
        if not isinstance(api_url, str) or not api_url.startswith(("http://", "https://")):
            logger.warning(f"Invalid API URL, using default: {ConfigDefaults.DEFAULT_API_URL}")
            api_url = ConfigDefaults.DEFAULT_API_URL
        validated["api_url"] = api_url
        
        # Category
        category = config.get("preferred_category")
        if category is not None and not isinstance(category, str):
            logger.warning("Invalid category, disabling category preference")
            category = None
        validated["preferred_category"] = category
        
        # Loop count
        loop_count = config.get("loop_count", ConfigDefaults.DEFAULT_LOOP_COUNT)
        try:
            loop_count = int(loop_count)
            if loop_count != 0 and not ConfigDefaults.MIN_LOOP_COUNT <= loop_count <= ConfigDefaults.MAX_LOOP_COUNT:
                logger.warning(
                    f"Loop count {loop_count} out of range "
                    f"({ConfigDefaults.MIN_LOOP_COUNT}-{ConfigDefaults.MAX_LOOP_COUNT}), "
                    f"using default: {ConfigDefaults.DEFAULT_LOOP_COUNT}"
                )
                loop_count = ConfigDefaults.DEFAULT_LOOP_COUNT
        except (TypeError, ValueError):
            logger.warning(f"Invalid loop count, using default: {ConfigDefaults.DEFAULT_LOOP_COUNT}")
            loop_count = ConfigDefaults.DEFAULT_LOOP_COUNT
        validated["loop_count"] = loop_count
        
        # Debug mode
        validated["debug"] = bool(config.get("debug", False))
        
        return validated

    def _ensure_config(self) -> None:
        """Ensure configuration directory and file exist with valid content."""
        try:
            Path(self.config_dir).mkdir(parents=True, exist_ok=True)
            
            if not os.path.exists(self.config_file):
                self.save_config(DEFAULT_CONFIG)
            else:
                current = self.load_config()
                updated = DEFAULT_CONFIG.copy()
                updated.update(current)
                validated = self._validate_config(updated)
                if current != validated:
                    self.save_config(validated)
                    
        except Exception as e:
            logger.error(f"Failed to initialize config: {e}")
            raise ConfigError(f"Configuration initialization failed: {str(e)}")

    def load_config(self) -> Dict[str, Any]:
        """Load and validate configuration from file.
        
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigError: If loading or validation fails
        """
        try:
            if not os.path.exists(self.config_file):
                return self._validate_config(DEFAULT_CONFIG)
                
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            return self._validate_config(config)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise ConfigError(f"Failed to parse configuration file: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise ConfigError(f"Configuration loading failed: {str(e)}")

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file after validation.
        
        Args:
            config: Configuration dictionary to save
            
        Raises:
            ConfigError: If validation or saving fails
        """
        try:
            validated = self._validate_config(config)
            with open(self.config_file, 'w') as f:
                json.dump(validated, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise ConfigError(f"Configuration saving failed: {str(e)}")
