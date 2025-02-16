import os

class LightingError(Exception):
    """Custom exception for lighting system errors"""
    pass

# Environment variable to control hardware simulation
SIMULATE_HARDWARE = os.getenv('SIMULATE_HARDWARE', 'false').lower() == 'true'

def safe_light_command(func):
    """Decorator to handle lighting system errors gracefully"""
    def wrapper(*args, **kwargs):
        try:
            if SIMULATE_HARDWARE:
                # Print what would have happened
                print(f"Light simulation: {func.__name__} called with args={args[1:]} kwargs={kwargs}")
                return
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Light system error in {func.__name__}: {str(e)}")
            try:
                # Try to set warning state
                args[0].setStatus('error')
            except:
                pass
            raise LightingError(str(e))
    return wrapper
