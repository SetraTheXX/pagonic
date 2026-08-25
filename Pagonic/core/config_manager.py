"""
ConfigManager - Pagonic Configuration Management
================================================
Central configuration management for GUI/CLI settings.


Features:
- JSON-based configuration persistence
- Default values with override support
- Recent files tracking
- Theme and language preferences
"""

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Pagonic configuration manager for persistent settings.
    
    Stores settings in user's home directory under .pagonic/config.json.
    Provides default values for all settings with easy override.
    
    Example:
        config = ConfigManager()
        
        # Get settings
        level = config.get("compression_level")  # Default: 6
        theme = config.get("theme")              # Default: "dark"
        
        # Set settings
        config.set("compression_level", 9)
        config.set("theme", "light")
        
        # Recent files
        config.add_recent_file("C:/path/to/archive.zip")
        recent = config.get("recent_files")
    """
    
    # Default configuration values
    DEFAULT_CONFIG: Dict[str, Any] = {
        # Compression settings
        "compression_level": 6,
        "smart_compression": True,
        "use_zip64": True,
        
        # UI settings
        "theme": "dark",
        "language": "tr",
        "show_progress": True,
        "confirm_overwrite": True,
        
        # Window settings
        "window_geometry": None,
        "window_maximized": False,
        "splitter_sizes": None,
        
        # Recent files
        "recent_files": [],
        "max_recent_files": 10,
        
        # Advanced settings
        "use_mmap": True,
        "parallel_extraction": False,
        "log_level": "INFO",
    }

    @classmethod
    def _default_config(cls) -> Dict[str, Any]:
        """Return an isolated copy of the default configuration."""
        return deepcopy(cls.DEFAULT_CONFIG)
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Custom config file path. If None, uses ~/.pagonic/config.json
        """
        if config_path is None:
            self.config_path = Path.home() / ".pagonic" / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config: Dict[str, Any] = self._load_config()
        logger.debug("ConfigManager initialized: %s", self.config_path)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or return defaults.
        
        Returns:
            Dict with merged default and saved configuration
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Merge with defaults (saved values override defaults)
                    merged = {**self._default_config(), **saved_config}
                    logger.debug("Loaded config from %s", self.config_path)
                    return merged
            except json.JSONDecodeError as e:
                logger.warning("Invalid config file, using defaults: %s", e)
                return self._default_config()
            except Exception as e:
                logger.warning("Failed to load config, using defaults: %s", e)
                return self._default_config()
        
        logger.debug("No config file found, using defaults")
        return self._default_config()
    
    def save(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Create directory if needed
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.debug("Config saved to %s", self.config_path)
            return True
        except Exception as e:
            logger.error("Failed to save config: %s", e)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
            auto_save: Automatically save after setting (default: True)
        """
        self.config[key] = value
        if auto_save:
            self.save()
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset configuration to defaults.
        
        Args:
            key: Specific key to reset. If None, resets all settings.
        """
        if key is None:
            self.config = self._default_config()
        elif key in self.DEFAULT_CONFIG:
            self.config[key] = deepcopy(self.DEFAULT_CONFIG[key])
        self.save()
    
    def add_recent_file(self, file_path: str) -> None:
        """
        Add file to recent files list.
        
        Args:
            file_path: Path to add to recent files
        """
        recent: List[str] = list(self.config.get("recent_files", []))
        max_recent = self.config.get("max_recent_files", 10)
        
        # Remove if already exists (to move to top)
        if file_path in recent:
            recent.remove(file_path)
        
        # Add to beginning
        recent.insert(0, file_path)
        
        # Limit size
        self.config["recent_files"] = recent[:max_recent]
        self.save()
    
    def get_recent_files(self) -> List[str]:
        """
        Get list of recent files.
        
        Returns:
            List of recent file paths
        """
        return list(self.config.get("recent_files", []))
    
    def clear_recent_files(self) -> None:
        """Clear recent files list."""
        self.config["recent_files"] = []
        self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get full configuration as dictionary.
        
        Returns:
            Copy of configuration dictionary
        """
        return deepcopy(self.config)
    
    def __repr__(self) -> str:
        return f"ConfigManager(path={self.config_path})"


# Singleton instance for global access
_global_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """
    Get global configuration manager instance.
    
    Returns:
        Global ConfigManager instance
        
    Example:
        from Pagonic.core.config_manager import get_config
        
        config = get_config()
        level = config.get("compression_level")
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config


# Quick test
if __name__ == "__main__":
    print("🧪 Testing ConfigManager...")
    
    # Create temporary config for testing
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_config_path = Path(tmpdir) / "test_config.json"
        
        # Test 1: Default values
        config = ConfigManager(str(test_config_path))
        assert config.get("compression_level") == 6
        assert config.get("theme") == "dark"
        print("  ✅ Default values work")
        
        # Test 2: Set and get
        config.set("compression_level", 9)
        assert config.get("compression_level") == 9
        print("  ✅ Set/Get works")
        
        # Test 3: Recent files
        config.add_recent_file("test1.zip")
        config.add_recent_file("test2.zip")
        recent = config.get_recent_files()
        assert len(recent) == 2
        assert recent[0] == "test2.zip"  # Most recent first
        print("  ✅ Recent files work")
        
        # Test 4: Persistence
        config2 = ConfigManager(str(test_config_path))
        assert config2.get("compression_level") == 9
        print("  ✅ Persistence works")
        
        # Test 5: Reset
        config.reset("compression_level")
        assert config.get("compression_level") == 6
        print("  ✅ Reset works")
    
    print("\n🎉 All ConfigManager tests passed!")
