"""RaspClaws Robot Control System

This package provides a complete control system for the RaspClaws robot platform,
including both server-side control logic and client-side user interface components.

The system is divided into two main packages:
- server: Contains robot control, sensor management, and web interface
- client: Contains GUI and configuration tools
"""

from . import server
from . import client

__version__ = '1.0.0'
__author__ = 'Adeept'
__license__ = 'MIT'