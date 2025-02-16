#!/usr/bin/env python3
from flask import Flask
from webServer import WebServer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize and start the web server
        server = WebServer()
        logger.info("Starting RaspClaws web server...")
        server.start(host='0.0.0.0', port=80)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == '__main__':
    main()