"""
Shared configuration loader for the Decision Intelligence module.
Reads config/decision_config.yaml once and caches it as a module-level singleton.
"""
import os
import yaml
from typing import Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("decision_config_loader")
_config_cache: Dict[str, Any] = {}


def load_decision_config() -> Dict[str, Any]:
    """
    Loads and caches the decision engine configuration from YAML.
    Returns a dict with all config sections (context, evidence, validation, etc.).
    Falls back to empty dict if the file is missing — callers must use .get() with defaults.
    """
    global _config_cache
    if _config_cache:
        logger.debug("Retrieving cached decision configuration.")
        return _config_cache

    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "config", "decision_config.yaml"
    )
    config_path = os.path.normpath(config_path)

    logger.info(f"Attempting to load decision config from: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f) or {}
            logger.info("Decision config loaded successfully.")
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}. Using empty default config.")
        _config_cache = {}

    return _config_cache
