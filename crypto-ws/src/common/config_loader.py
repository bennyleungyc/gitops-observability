"""Configuration loader with priority-based merging.

Loads configuration from multiple sources with the following priority (highest to lowest):
1. Environment variables
2. Custom config file (--config flag)
3. Local config file (config/local.yml)
4. Environment-specific config (config/{env}.yml)
5. Default config (config/default.yml)
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigLoader:
    """Load and merge configuration from multiple sources."""
    
    def __init__(self, module_dir: Path, exchange_name: str):
        """
        Initialize config loader for a specific listener module.
        
        Args:
            module_dir: Path to the listener module directory (e.g., src/binance_listener)
            exchange_name: Exchange name for environment variable prefix (e.g., 'binance')
        """
        self.module_dir = Path(module_dir)
        self.config_dir = self.module_dir / "config"
        self.exchange_name = exchange_name.upper()
        
    def load(self, custom_config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from all sources and merge with priority.
        
        Args:
            custom_config_path: Optional path to custom config file
            
        Returns:
            Merged configuration dictionary
        """
        config = {}
        
        # 1. Load default config (lowest priority)
        default_path = self.config_dir / "default.yml"
        if default_path.exists():
            config = self._load_yaml(default_path)
        
        # 2. Load environment-specific config
        env = os.getenv("CONFIG_ENV", "").lower()
        if env:
            env_path = self.config_dir / f"{env}.yml"
            if env_path.exists():
                config = self._merge_configs(config, self._load_yaml(env_path))
        
        # 3. Load local config (gitignored developer overrides)
        local_path = self.config_dir / "local.yml"
        if local_path.exists():
            config = self._merge_configs(config, self._load_yaml(local_path))
        
        # 4. Load custom config file if provided
        if custom_config_path:
            custom_path = Path(custom_config_path)
            if custom_path.exists():
                config = self._merge_configs(config, self._load_yaml(custom_path))
        
        # 5. Apply environment variable overrides (highest priority)
        config = self._apply_env_overrides(config)
        
        return config
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML file and return as dictionary."""
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries.
        Override values take precedence over base values.
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override value
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to config.
        
        Supports:
        - {EXCHANGE}_SYMBOLS or {EXCHANGE}_INSTRUMENTS: comma-separated list
        - {EXCHANGE}_DEPTH: global depth override
        - {EXCHANGE}_WS_ENDPOINT: endpoint override
        """
        # Override endpoint
        endpoint_var = f"{self.exchange_name}_WS_ENDPOINT"
        if endpoint_var in os.environ:
            if "connection" not in config:
                config["connection"] = {}
            config["connection"]["endpoint"] = os.environ[endpoint_var]
        
        # Override symbols/instruments (backward compatibility)
        symbols_var = f"{self.exchange_name}_SYMBOLS"
        instruments_var = f"{self.exchange_name}_INSTRUMENTS"
        
        if symbols_var in os.environ:
            # Parse comma-separated symbols
            symbols_str = os.environ[symbols_var]
            symbols = [s.strip().lower() for s in symbols_str.split(",") if s.strip()]
            
            # Get depth from env or use existing
            depth = os.getenv(f"{self.exchange_name}_DEPTH")
            
            # Build symbol list
            config["symbols"] = []
            for symbol in symbols:
                symbol_config = {"symbol": symbol, "enabled": True}
                if depth:
                    symbol_config["depth"] = int(depth)
                config["symbols"].append(symbol_config)
        
        elif instruments_var in os.environ:
            # Parse comma-separated instruments
            instruments_str = os.environ[instruments_var]
            instruments = [i.strip().upper() for i in instruments_str.split(",") if i.strip()]
            
            # Get depth from env or use existing
            depth = os.getenv(f"{self.exchange_name}_DEPTH")
            
            # Build instrument list
            config["instruments"] = []
            for instrument in instruments:
                inst_config = {"instrument": instrument, "enabled": True}
                if depth:
                    inst_config["depth"] = int(depth)
                config["instruments"].append(inst_config)
        
        # Override global depth if specified and no symbols/instruments env var
        elif f"{self.exchange_name}_DEPTH" in os.environ:
            depth = int(os.environ[f"{self.exchange_name}_DEPTH"])
            
            # Apply to existing symbols/instruments
            if "symbols" in config:
                for symbol in config["symbols"]:
                    symbol["depth"] = depth
            if "instruments" in config:
                for instrument in config["instruments"]:
                    instrument["depth"] = depth
        
        return config
    
    def get_symbols_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize symbols configuration.
        
        Returns list of symbol configs with 'symbol', 'depth', 'enabled' keys.
        """
        symbols = config.get("symbols", [])
        default_depth = config.get("default_depth", 10)
        
        # Normalize symbol configs
        normalized = []
        for item in symbols:
            if isinstance(item, str):
                # Simple string: convert to full config
                normalized.append({
                    "symbol": item.lower(),
                    "depth": default_depth,
                    "enabled": True
                })
            elif isinstance(item, dict):
                # Already a config dict
                symbol_config = {
                    "symbol": item.get("symbol", "").lower(),
                    "depth": item.get("depth", default_depth),
                    "enabled": item.get("enabled", True)
                }
                normalized.append(symbol_config)
        
        # Filter to only enabled symbols
        return [s for s in normalized if s["enabled"]]
    
    def get_instruments_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and normalize instruments configuration.
        
        Returns list of instrument configs with 'instrument', 'depth', 'enabled' keys.
        """
        instruments = config.get("instruments", [])
        default_depth = config.get("default_depth", 10)
        
        # Normalize instrument configs
        normalized = []
        for item in instruments:
            if isinstance(item, str):
                # Simple string: convert to full config
                normalized.append({
                    "instrument": item.upper(),
                    "depth": default_depth,
                    "enabled": True
                })
            elif isinstance(item, dict):
                # Already a config dict
                inst_config = {
                    "instrument": item.get("instrument", "").upper(),
                    "depth": item.get("depth", default_depth),
                    "enabled": item.get("enabled", True)
                }
                normalized.append(inst_config)
        
        # Filter to only enabled instruments
        return [i for i in normalized if i["enabled"]]

