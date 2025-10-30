#!/usr/bin/env python3
"""
Structured Logging Utilities for Data Pipeline
Provides rotating file handlers with JSON and console output
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


class StructuredLogger:
    """Logger with structured JSON output and human-readable console output"""
    
    def __init__(self, name, log_dir="logs", log_level=logging.INFO):
        """
        Initialize structured logger
        
        Args:
            name: Logger name (used for log file naming)
            log_dir: Base directory for log files
            log_level: Logging level (default: INFO)
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Add handlers
        self._add_console_handler()
        self._add_file_handler()
        self._add_json_handler()
    
    def _add_console_handler(self):
        """Add human-readable console output"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """Add rotating file handler for human-readable logs"""
        log_file = self.log_dir / f"{self.name}.log"
        
        # Max 10MB per file, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _add_json_handler(self):
        """Add JSON structured log handler for programmatic parsing"""
        json_log_file = self.log_dir / f"{self.name}.json"
        
        # Max 10MB per file, keep 5 backup files
        json_handler = RotatingFileHandler(
            json_log_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
    
    def log_operation(self, level, operation, message, **metadata):
        """
        Log an operation with structured metadata
        
        Args:
            level: Log level (e.g., logging.INFO)
            operation: Operation name (e.g., 'file_copy', 'validation')
            message: Human-readable message
            **metadata: Additional structured data
        """
        extra = {
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat(),
            **metadata
        }
        self.logger.log(level, message, extra=extra)
    
    def info(self, message, **metadata):
        """Log info level message with metadata"""
        self.log_operation(logging.INFO, 'general', message, **metadata)
    
    def debug(self, message, **metadata):
        """Log debug level message with metadata"""
        self.log_operation(logging.DEBUG, 'general', message, **metadata)
    
    def warning(self, message, **metadata):
        """Log warning level message with metadata"""
        self.log_operation(logging.WARNING, 'general', message, **metadata)
    
    def error(self, message, **metadata):
        """Log error level message with metadata"""
        self.log_operation(logging.ERROR, 'general', message, **metadata)
    
    def critical(self, message, **metadata):
        """Log critical level message with metadata"""
        self.log_operation(logging.CRITICAL, 'general', message, **metadata)


class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        
        # Add any additional metadata from extra parameter
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info', 'operation', 'timestamp']:
                try:
                    # Only add JSON-serializable values
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    pass
        
        return json.dumps(log_data)


def get_logger(name, log_dir="logs", log_level=logging.INFO):
    """
    Get or create a structured logger
    
    Args:
        name: Logger name
        log_dir: Base directory for logs
        log_level: Logging level
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, log_dir, log_level)


if __name__ == "__main__":
    # Test the logger
    logger = get_logger('test_logger', log_dir='logs/test')
    
    logger.info("Test info message", file_count=5, status="success")
    logger.warning("Test warning", validation_errors=["missing_field"])
    logger.error("Test error", error_code=500)
    
    print("\nLogger test complete. Check logs/test/ directory.")
