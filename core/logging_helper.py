"""
Application logging module.

All log entries are written to data/logs/app.log with automatic rotation.
Supports INFO, WARNING, ERROR levels.
"""

import os
import logging
import sys
from datetime import datetime
from ui.asset_path import data_dir


class AppLogger:
    """Thread-safe logger that writes to a file and optionally to console."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        log_dir = os.path.join(data_dir(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")
        
        # Create logger
        self.logger = logging.getLogger("SecureTranslatorPro")
        self.logger.setLevel(logging.DEBUG)
        
        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            # File handler with rotation
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5 MB
                backupCount=3,
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Console handler (only WARNING and above)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            
            # Formatter
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
