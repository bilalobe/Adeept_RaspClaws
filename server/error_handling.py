"""Error handling utilities for RaspClaws"""
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

class RobotError(Exception):
    """Base exception for robot-related errors"""
    pass

class HardwareError(RobotError):
    """Error related to hardware components"""
    pass

class MotionError(RobotError):
    """Error related to robot movement"""
    pass

class BalanceError(RobotError):
    """Error related to balance control"""
    pass

def retry_on_hardware_error(max_attempts=3, delay=1):
    """Decorator to retry hardware operations with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except HardwareError as e:
                    attempt += 1
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    wait_time = delay * (2 ** attempt)
                    logger.warning(f"Hardware error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

def safe_motion(func):
    """Decorator to handle motion errors gracefully"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Motion error in {func.__name__}: {e}")
            raise MotionError(f"Failed to execute {func.__name__}: {str(e)}")
    return wrapper

def monitor_balance(threshold=30):
    """Decorator to monitor balance during operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from initialization import sensor, mpu6050_connection
            if not mpu6050_connection:
                return func(*args, **kwargs)
            
            try:
                initial = sensor.get_accel_data()
                result = func(*args, **kwargs)
                final = sensor.get_accel_data()
                
                # Check if balance was maintained
                delta_x = abs(final['x'] - initial['x'])
                delta_y = abs(final['y'] - initial['y'])
                
                if delta_x > threshold or delta_y > threshold:
                    raise BalanceError(f"Balance exceeded threshold: dx={delta_x:.2f}, dy={delta_y:.2f}")
                
                return result
            except Exception as e:
                logger.error(f"Balance error in {func.__name__}: {e}")
                raise
        return wrapper
    return decorator