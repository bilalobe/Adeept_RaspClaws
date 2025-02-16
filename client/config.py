"""Configuration parameters for RaspClaws client"""

# Network Configuration
DEFAULT_SERVER_PORT = 10223
DEFAULT_INFO_PORT = 2256
BUFFER_SIZE = 1024
CONNECTION_RETRIES = 5
RETRY_DELAY = 1.0  # seconds

# GUI Configuration
WINDOW_SIZE = "565x680"
WINDOW_TITLE = "Adeept RaspClaws"

# Color Theme
COLORS = {
    'background': '#000000',
    'text': '#E1F5FE',
    'button': '#0277BD',
    'line': '#01579B',
    'canvas': '#212121',
    'oval': '#2196F3',
    'target': '#FF6D00',
    'connected': '#558B2F',
    'disconnected': '#F44336',
    'connecting': '#FF8F00',
    'slider_red': '#F44336',
    'slider_green': '#00E676',
    'slider_blue': '#448AFF'
}

# Control Parameters
SMOOTH_MODE_DEFAULT = 0
FUNCTION_MODE_DEFAULT = 0

# RGB Control Ranges
RGB_RANGE = {
    'min': 0,
    'max': 255,
    'default': 0
}

# Exposure Compensation
EC_RANGE = {
    'min': -25,
    'max': 25,
    'default': 0
}

# Line Following Parameters
LINE_FOLLOWING = {
    'lip1_default': 440,
    'lip2_default': 380,
    'error_default': 20,
    'lip_range': (0, 480),
    'error_range': (0, 200)
}

# Command Delay
COMMAND_DELAY = 0.03  # seconds between commands

# Thread Configuration
THREAD_CONFIG = {
    'connection': True,  # daemon status
    'video': True,
    'info': True,
    'opencv': True
}
