# Dependencies: 
# pip install flask websockets flask-cors
# Optional for development: pip install pylint pytest

#!/usr/bin/env/python
# File name   : server.py
# Production  : GWR
# Website	 : www.adeept.com
# Author	  : William
# Date		: 2020/03/17

import os
import json
import logging
import asyncio
import websockets
from flask import Flask, request, jsonify
from functools import wraps

import RPIservo
import functions
import info
import move
import robotLight
from server import FPV
from lighting_utils import LightingError
from error_handling import retry_on_hardware_error, safe_motion
import initialization

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebServer:
    def __init__(self, host='0.0.0.0', http_port=5000, ws_port=8888):
        self.host = host
        self.http_port = http_port
        self.ws_port = ws_port
        
        # Initialize Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Initialize components
        self.fpv = FPV()
        self.sc = RPIservo.ServoCtrl()
        self.sc.moveInit()
        
        try:
            self.led = robotLight.RobotLight()
            self.led.start()
            self.led.breath(70, 70, 255)
        except Exception as e:
            logger.error(f"LED initialization failed: {e}")
            self.led = None

        # Initialize servo controllers
        self.P_sc = RPIservo.ServoCtrl()
        self.T_sc = RPIservo.ServoCtrl()
        self.P_sc.start()
        self.T_sc.start()

        # State variables
        self.direction_command = 'no'
        self.turn_command = 'no'
        self.move_stu = 1
        self.functionMode = 0
        
    def setup_routes(self):
        """Set up Flask routes"""
        self.app.route('/')(self.index)
        self.app.route('/hop', methods=['POST'])(self.hop_command)
        self.app.route('/hop/status')(self.hop_status)
        self.app.route('/lights/brightness', methods=['POST'])(self.set_brightness)
        self.app.route('/lights/color', methods=['POST'])(self.set_color)
        self.app.route('/lights/pattern', methods=['POST'])(self.set_pattern)
        self.app.route('/parameters')(self.parameters_page)
        self.app.route('/param_update')(self.update_parameter)

    @retry_on_hardware_error()
    def hop_command(self):
        """Handle hop command with error handling"""
        data = request.get_json()
        speed = min(max(data.get('speed', 20), 1), 100)
        air_time = min(max(data.get('air_time', 0.3), 0.1), 1.0)
        
        try:
            move.hop(speed=speed, air_time=air_time)
            return jsonify({
                'success': True,
                'message': 'Hop executed',
                'parameters': {'speed': speed, 'air_time': air_time}
            })
        except Exception as e:
            logger.error(f"Hop command failed: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    def hop_status(self):
        """Get hopping and balance status"""
        if not initialization.mpu6050_connection:
            return jsonify({'connected': False})
            
        try:
            accel_data = initialization.sensor.get_accel_data()
            filtered_x = initialization.kalman_filter_X.kalman(accel_data['x'])
            filtered_y = initialization.kalman_filter_Y.kalman(accel_data['y'])
            return jsonify({
                'connected': True,
                'x': filtered_x,
                'y': filtered_y,
                'raw_x': accel_data['x'],
                'raw_y': accel_data['y']
            })
        except Exception as e:
            logger.error(f"Error getting sensor data: {e}")
            return jsonify({'connected': False, 'error': str(e)}), 500

    async def ws_handler(self, websocket, path):
        """Handle WebSocket connections"""
        try:
            if not await self.check_permit(websocket):
                return
                
            await self.handle_messages(websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def check_permit(self, websocket):
        """Authenticate WebSocket connection"""
        try:
            recv_str = await websocket.recv()
            cred_dict = recv_str.split(":")
            if cred_dict[0] == "admin" and cred_dict[1] == "123456":
                await websocket.send("Connection authenticated")
                return True
            await websocket.send("Authentication failed")
            return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def handle_messages(self, websocket):
        """Handle incoming WebSocket messages"""
        while True:
            try:
                data = await websocket.recv()
                response = await self.process_command(data)
                await websocket.send(json.dumps(response))
            except Exception as e:
                logger.error(f"Message handling error: {e}")
                break

    @safe_motion
    async def process_command(self, data):
        """Process incoming commands"""
        response = {'status': 'ok', 'title': '', 'data': None}
        
        try:
            if isinstance(data, str):
                if data == 'get_info':
                    response['title'] = 'get_info'
                    response['data'] = info.monitor.get_status()
                else:
                    # Handle movement commands
                    self.handle_movement_command(data)
                    # Handle function commands
                    self.handle_function_command(data)
            
            elif isinstance(data, dict):
                # Handle structured commands
                self.handle_structured_command(data)
                
        except Exception as e:
            logger.error(f"Command processing error: {e}")
            response['status'] = 'error'
            response['error'] = str(e)
            
        return response

    def start(self):
        """Start both Flask and WebSocket servers"""
        # Start WebSocket server
        ws_server = websockets.serve(self.ws_handler, self.host, self.ws_port)
        asyncio.get_event_loop().run_until_complete(ws_server)
        
        # Start Flask server
        self.app.run(host=self.host, port=self.http_port, debug=False, threaded=True)

    def cleanup(self):
        """Clean up resources"""
        if self.led:
            self.led.cleanup()
        self.sc.cleanup()
        self.P_sc.cleanup()
        self.T_sc.cleanup()
        move.destroy()

# Create global web server instance
web_server = None

def init_server():
    """Initialize and return web server instance"""
    global web_server
    if web_server is None:
        web_server = WebServer()
    return web_server

if __name__ == '__main__':
    try:
        server = init_server()
        server.start()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        if server:
            server.cleanup()
    except Exception as e:
        logger.error(f"Server error: {e}")
        if server:
            server.cleanup()
