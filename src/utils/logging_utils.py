import logging
import logging.config
import yaml
from pathlib import Path
import os
from typing import Optional
from functools import wraps
import time
import traceback

def setup_logging(
    default_path: str = 'configs/logging_config.yml',
    default_level: int = logging.INFO,
    env_key: str = 'LOG_CFG'
) -> None:
    """Setup logging configuration"""
    path = os.getenv(env_key, default_path)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                print(f'Error in Logging Configuration: {e}')
                print('Using default logging configuration')
                logging.basicConfig(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        print('Failed to load configuration file. Using default configs')

def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)

def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            current_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                current_logger.debug(
                    f'Function {func.__name__} executed in {execution_time:.2f} seconds'
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                current_logger.error(
                    f'Function {func.__name__} failed after {execution_time:.2f} seconds. '
                    f'Error: {str(e)}\n{traceback.format_exc()}'
                )
                raise
        return wrapper
    return decorator

def log_async_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log async function execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            current_logger = logger or logging.getLogger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                current_logger.debug(
                    f'Async function {func.__name__} executed in {execution_time:.2f} seconds'
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                current_logger.error(
                    f'Async function {func.__name__} failed after {execution_time:.2f} seconds. '
                    f'Error: {str(e)}\n{traceback.format_exc()}'
                )
                raise
        return wrapper
    return decorator