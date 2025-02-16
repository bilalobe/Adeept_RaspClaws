#!/usr/bin/python
# -*- coding: UTF-8 -*-
# File name   : client.py
# Description : client  
# Website	 : www.adeept.com
# E-mail	  : support@adeept.com
# Author	  : Devin
# Date		: 2023/06/14

import json
import os
import threading as thread
import time
import tkinter as tk
import socket
from tkinter import ttk

from client.config import COLORS, COMMAND_DELAY, CONNECTION_RETRIES, DEFAULT_INFO_PORT, DEFAULT_SERVER_PORT, EC_RANGE, \
    LINE_FOLLOWING, RGB_RANGE

from config import *

try:  # 1
    import cv2
    import zmq
    import base64
    import numpy as np
except:
    print("Couldn't import OpenCV, you need to install it first.")


class ConfigEditor:
    def __init__(self, parent, callback=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Configuration Editor")
        self.window.geometry("400x600")

        # Create a notebook for tabbed interface
        self.notebook = ttk.Notebook(self.window)

        # Create tabs
        self.network_tab = self.create_tab("Network")
        self.control_tab = self.create_tab("Control")
        self.color_tab = self.create_tab("Colors")

        self.notebook.pack(expand=True, fill='both')

        # Add save button
        self.save_btn = tk.Button(self.window, text="Save Changes", command=self.save_config)
        self.save_btn.pack(pady=10)

        self.callback = callback  # Callback for hot-reloading

        # Add apply button for live updates
        self.apply_btn = tk.Button(self.window, text="Apply", command=self.apply_changes)
        self.apply_btn.pack(pady=5)

        # Add runtime tuning section
        self.create_runtime_tab()

        self.load_config()

    def create_tab(self, name):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=name)
        return tab

    def load_config(self):
        # Network parameters
        self.create_entry(self.network_tab, "Server Port", "DEFAULT_SERVER_PORT")
        self.create_entry(self.network_tab, "Info Port", "DEFAULT_INFO_PORT")
        self.create_entry(self.network_tab, "Connection Retries", "CONNECTION_RETRIES")

        # Control parameters
        self.create_entry(self.control_tab, "Command Delay", "COMMAND_DELAY")
        self.create_range_entries(self.control_tab, "RGB Range", "RGB_RANGE")
        self.create_range_entries(self.control_tab, "Exposure Compensation", "EC_RANGE")
        self.create_range_entries(self.control_tab, "Line Following", "LINE_FOLLOWING")

        # Color parameters
        for color_name, color_value in COLORS.items():
            self.create_color_picker(self.color_tab, color_name, color_value)

    def create_entry(self, parent, label, config_key):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(frame, text=label).pack(side='left')
        entry = ttk.Entry(frame)
        entry.pack(side='right')
        entry.insert(0, str(globals()[config_key]))

        return entry

    def create_range_entries(self, parent, label, config_key):
        frame = ttk.LabelFrame(parent, text=label)
        frame.pack(fill='x', padx=5, pady=5)

        config_dict = globals()[config_key]
        entries = {}

        for key in config_dict:
            row = ttk.Frame(frame)
            row.pack(fill='x', padx=5, pady=2)
            ttk.Label(row, text=key).pack(side='left')
            entry = ttk.Entry(row)
            entry.pack(side='right')
            entry.insert(0, str(config_dict[key]))
            entries[key] = entry

        return entries

    def create_color_picker(self, parent, color_name, color_value):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', padx=5, pady=2)

        ttk.Label(frame, text=color_name).pack(side='left')
        entry = ttk.Entry(frame)
        entry.pack(side='right')
        entry.insert(0, color_value)

        return entry

    def create_runtime_tab(self):
        runtime_tab = self.create_tab("Runtime")

        # Movement sensitivity
        sensitivity_frame = ttk.LabelFrame(runtime_tab, text="Movement Sensitivity")
        sensitivity_frame.pack(fill='x', padx=5, pady=5)

        self.movement_scale = ttk.Scale(sensitivity_frame, from_=0.1, to=2.0,
                                        orient='horizontal')
        self.movement_scale.set(1.0)
        self.movement_scale.pack(fill='x', padx=5, pady=5)

        # Head movement speed
        head_frame = ttk.LabelFrame(runtime_tab, text="Head Movement Speed")
        head_frame.pack(fill='x', padx=5, pady=5)

        self.head_scale = ttk.Scale(head_frame, from_=0.1, to=2.0,
                                    orient='horizontal')
        self.head_scale.set(1.0)
        self.head_scale.pack(fill='x', padx=5, pady=5)

        # Color detection threshold
        color_frame = ttk.LabelFrame(runtime_tab, text="Color Detection")
        color_frame.pack(fill='x', padx=5, pady=5)

        self.color_threshold = ttk.Scale(color_frame, from_=0, to=100,
                                         orient='horizontal')
        self.color_threshold.set(50)
        self.color_threshold.pack(fill='x', padx=5, pady=5)

    def apply_changes(self):
        """Apply changes without saving to file"""
        if self.callback:
            config_data = self.get_current_config()
            self.callback(config_data)

    def get_current_config(self):
        """Get current configuration including runtime values"""
        config = {
            # ... existing config gathering ...
            "runtime": {
                "movement_sensitivity": self.movement_scale.get(),
                "head_speed": self.head_scale.get(),
                "color_threshold": self.color_threshold.get()
            }
        }
        return config

    def save_config(self):
        # Save configuration to a JSON file
        config_data = {
            "network": {
                "DEFAULT_SERVER_PORT": int(self.network_entries["Server Port"].get()),
                "DEFAULT_INFO_PORT": int(self.network_entries["Info Port"].get()),
                "CONNECTION_RETRIES": int(self.network_entries["Connection Retries"].get())
            },
            "control": {
                "COMMAND_DELAY": float(self.control_entries["Command Delay"].get()),
                "RGB_RANGE": {k: int(v.get()) for k, v in self.rgb_entries.items()},
                "EC_RANGE": {k: int(v.get()) for k, v in self.ec_entries.items()},
                "LINE_FOLLOWING": {k: int(v.get()) for k, v in self.line_entries.items()}
            },
            "colors": {k: v.get() for k, v in self.color_entries.items()}
        }

        with open('config_override.json', 'w') as f:
            json.dump(config_data, f, indent=4)

        self.window.destroy()


class GUIController:
    def __init__(self):
        # Load configuration
        self.load_config()

        # Initialize state variables
        self.ip_stu = 1
        self.c_f_stu = 0
        self.c_b_stu = 0
        self.c_l_stu = 0
        self.c_r_stu = 0
        self.c_ls_stu = 0
        self.c_rs_stu = 0
        self.funcMode = 0
        self.Switch_3 = 0
        self.Switch_2 = 0
        self.Switch_1 = 0
        self.SmoothMode = 0
        self.tcpClicSock = None
        self.footage_socket = None
        self.root = None

        # GUI elements that need class-wide access
        self.E1 = None
        self.l_ip_4 = None
        self.l_ip_5 = None
        self.CPU_TEP_lab = None
        self.CPU_USE_lab = None
        self.RAM_lab = None
        self.Btn_Steady = None
        self.Btn_FindColor = None
        self.Btn_WatchDog = None
        self.Btn_Fun4 = None
        self.Btn_Fun5 = None
        self.Btn_Fun6 = None
        self.Btn_Switch_1 = None
        self.Btn_Switch_2 = None
        self.Btn_Switch_3 = None
        self.Btn_Smooth = None

        # Initialize variables
        self.var_lip1 = tk.StringVar(value='440')
        self.var_lip2 = tk.StringVar(value='380')
        self.var_err = tk.StringVar(value='20')
        self.var_R = tk.StringVar(value='0')
        self.var_G = tk.StringVar(value='0')
        self.var_B = tk.StringVar(value='0')
        self.var_ec = tk.StringVar(value='0')

        # Colors
        self.color_bg = '#000000'
        self.color_text = '#E1F5FE'
        self.color_btn = '#0277BD'
        self.color_line = '#01579B'
        self.color_can = '#212121'
        self.color_oval = '#2196F3'
        self.target_color = '#FF6D00'

        self.runtime_config = {
            "movement_sensitivity": 1.0,
            "head_speed": 1.0,
            "color_threshold": 50
        }

        self.parameter_panel = None

        # Add parameter button variables
        self.show_params_btn = None

    def load_config(self):
        # Load default config
        self.config = {
            "network": {
                "server_port": DEFAULT_SERVER_PORT,
                "info_port": DEFAULT_INFO_PORT,
                "retries": CONNECTION_RETRIES
            },
            "control": {
                "command_delay": COMMAND_DELAY,
                "rgb_range": RGB_RANGE,
                "ec_range": EC_RANGE,
                "line_following": LINE_FOLLOWING
            },
            "colors": COLORS
        }

        # Override with custom config if exists
        if os.path.exists('config_override.json'):
            with open('config_override.json', 'r') as f:
                override = json.load(f)
                self.config.update(override)

    def show_config_editor(self):
        ConfigEditor(self.root, callback=self.update_runtime_config)

    def update_runtime_config(self, config_data):
        """Hot-reload configuration changes"""
        self.config.update(config_data)
        self.runtime_config.update(config_data.get("runtime", {}))
        self.apply_runtime_changes()

    def apply_runtime_changes(self):
        """Apply runtime configuration changes"""
        # Update movement commands with sensitivity
        sensitivity = self.runtime_config["movement_sensitivity"]
        head_speed = self.runtime_config["head_speed"]

        # Scale movement commands
        movement_commands = {
            'forward': lambda: self.tcpClicSock.send(('forward %.2f' % sensitivity).encode()),
            'backward': lambda: self.tcpClicSock.send(('backward %.2f' % sensitivity).encode()),
            'left': lambda: self.tcpClicSock.send(('left %.2f' % sensitivity).encode()),
            'right': lambda: self.tcpClicSock.send(('right %.2f' % sensitivity).encode())
        }

        # Scale head movement commands
        head_commands = {
            'headup': lambda: self.tcpClicSock.send(('headup %.2f' % head_speed).encode()),
            'headdown': lambda: self.tcpClicSock.send(('headdown %.2f' % head_speed).encode()),
            'headleft': lambda: self.tcpClicSock.send(('headleft %.2f' % head_speed).encode()),
            'headright': lambda: self.tcpClicSock.send(('headright %.2f' % head_speed).encode())
        }

        # Update the command functions
        self.movement_commands = movement_commands
        self.head_commands = head_commands

    def video_thread(self):
        context = zmq.Context()
        self.footage_socket = context.socket(zmq.SUB)
        self.footage_socket.connect('tcp://%s:5555' % self.ip_adr)
        self.footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.frame_num = 0
        self.fps = 0

    def get_FPS(self):
        while 1:
            try:
                time.sleep(1)
                self.fps = self.frame_num
                self.frame_num = 0
            except:
                time.sleep(1)

    def opencv_r(self):
        while True:
            try:
                frame = self.footage_socket.recv_string()
                img = base64.b64decode(frame)
                npimg = np.frombuffer(img, dtype=np.uint8)
                source = cv2.imdecode(npimg, 1)
                cv2.putText(source, ('PC FPS: %s' % self.fps), (40, 20), self.font, 0.5, (255, 255, 255), 1,
                            cv2.LINE_AA)
                try:
                    cv2.putText(source, ('CPU Temperature: %s' % self.CPU_TEP), (370, 350), self.font, 0.5,
                                (128, 255, 128), 1, cv2.LINE_AA)
                    cv2.putText(source, ('CPU Usage: %s' % self.CPU_USE), (370, 380), self.font, 0.5, (128, 255, 128),
                                1, cv2.LINE_AA)
                    cv2.putText(source, ('RAM Usage: %s' % self.RAM_USE), (370, 410), self.font, 0.5, (128, 255, 128),
                                1, cv2.LINE_AA)
                except:
                    pass
                cv2.imshow("Stream", source)
                self.frame_num += 1
                cv2.waitKey(1)
            except:
                time.sleep(0.5)
                break

    def replace_num(self, initial, new_num):  # Call this function to replace data in '.txt' file
        newline = ""
        str_num = str(new_num)
        with open("./ip.txt", "r") as f:
            for line in f.readlines():
                if (line.find(initial) == 0):
                    line = initial + "%s" % (str_num)
                newline += line
        with open("./ip.txt", "w") as f:
            f.writelines(newline)  # Call this function to replace data in '.txt' file

    def num_import(self, initial):  # Call this function to import data from '.txt' file
        with open("./ip.txt") as f:
            for line in f.readlines():
                if (line.find(initial) == 0):
                    r = line
        begin = len(list(initial))
        snum = r[begin:]
        n = snum
        return n

    def call_forward(self, event):  # When this function is called,client commands the car to move forward
        if self.c_f_stu == 0:
            self.movement_commands['forward']()
            self.c_f_stu = 1

    def call_back(self, event):  # When this function is called,client commands the car to move backward
        if self.c_b_stu == 0:
            self.movement_commands['backward']()
            self.c_b_stu = 1

    def call_FB_stop(self, event):  # When this function is called,client commands the car to stop moving
        self.c_f_stu = 0
        self.c_b_stu = 0
        self.tcpClicSock.send(('DS').encode())

    def call_Turn_stop(self, event):  # When this function is called,client commands the car to stop moving
        self.c_l_stu = 0
        self.c_r_stu = 0
        self.c_ls_stu = 0
        self.c_rs_stu = 0
        self.tcpClicSock.send(('TS').encode())

    def call_Left(self, event):  # When this function is called,client commands the car to turn left
        if self.c_l_stu == 0:
            self.movement_commands['left']()
            self.c_l_stu = 1

    def call_Right(self, event):  # When this function is called,client commands the car to turn right
        if self.c_r_stu == 0:
            self.movement_commands['right']()
            self.c_r_stu = 1

    def call_LeftSide(self, event):
        if self.c_ls_stu == 0:
            self.tcpClicSock.send(('leftside').encode())
            self.c_ls_stu = 1

    def call_RightSide(self, event):
        if self.c_rs_stu == 0:
            self.tcpClicSock.send(('rightside').encode())
            self.c_rs_stu = 1

    def call_headup(self, event):
        self.head_commands['headup']()

    def call_headdown(self, event):
        self.head_commands['headdown']()

    def call_headleft(self, event):
        self.head_commands['headleft']()

    def call_headright(self, event):
        self.head_commands['headright']()

    def call_headhome(self, event):
        self.tcpClicSock.send(('headhome').encode())

    def call_steady(self, event):
        if self.funcMode == 0:
            self.tcpClicSock.send(('steady').encode())
        else:
            self.tcpClicSock.send(('funEnd').encode())

    def call_FindColor(self, event):
        if self.funcMode == 0:
            self.tcpClicSock.send(('FindColor').encode())
        else:
            self.tcpClicSock.send(('funEnd').encode())

    def call_WatchDog(self, event):
        if self.funcMode == 0:
            self.tcpClicSock.send(('WatchDog').encode())
        else:
            self.tcpClicSock.send(('funEnd').encode())

    def call_Smooth(self, event):
        if self.SmoothMode == 0:
            self.tcpClicSock.send(('Smooth_on').encode())
        else:
            self.tcpClicSock.send(('Smooth_off').encode())

    def call_Switch_1(self, event):
        if self.Switch_1 == 0:
            self.tcpClicSock.send(('Switch_1_on').encode())
        else:
            self.tcpClicSock.send(('Switch_1_off').encode())

    def call_Switch_2(self, event):
        if self.Switch_2 == 0:
            self.tcpClicSock.send(('Switch_2_on').encode())
        else:
            self.tcpClicSock.send(('Switch_2_off').encode())

    def call_Switch_3(self, event):
        if self.Switch_3 == 0:
            self.tcpClicSock.send(('Switch_3_on').encode())
        else:
            self.tcpClicSock.send(('Switch_3_off').encode())

    def all_btn_red(self):
        self.Btn_Steady.config(bg='#FF6D00', fg='#000000')
        self.Btn_FindColor.config(bg='#FF6D00', fg='#000000')
        self.Btn_WatchDog.config(bg='#FF6D00', fg='#000000')
        self.Btn_Fun4.config(bg='#FF6D00', fg='#000000')
        self.Btn_Fun5.config(bg='#FF6D00', fg='#000000')
        self.Btn_Fun6.config(bg='#FF6D00', fg='#000000')

    def all_btn_normal(self):
        self.Btn_Steady.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_FindColor.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_WatchDog.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_Fun4.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_Fun5.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_Fun6.config(bg=self.color_btn, fg=self.color_text)

    def connection_thread(self):
        while True:
            try:
                car_info = self.tcpClicSock.recv(1024).decode()
                if not car_info:
                    continue
                self.handle_car_info(car_info)
            except:
                pass

    def handle_car_info(self, car_info):
        info_handlers = {
            'FindColor': (lambda: self.set_function_mode(1, self.Btn_FindColor)),
            'steady': (lambda: self.set_function_mode(1, self.Btn_Steady)),
            'WatchDog': (lambda: self.set_function_mode(1, self.Btn_WatchDog)),
            'Smooth_on': lambda: self.set_smooth_mode(1),
            'Smooth_off': lambda: self.set_smooth_mode(0),
            'FunEnd': lambda: self.set_function_mode(0)
        }

        for key, handler in info_handlers.items():
            if key in car_info:
                handler()
                break

    def set_function_mode(self, mode, active_btn=None):
        self.funcMode = mode
        if mode == 1:
            self.all_btn_red()
            if active_btn:
                active_btn.config(bg='#00E676')
        else:
            self.all_btn_normal()

    def Info_receive(self):
        HOST = ''
        INFO_PORT = 2256  # Define port serial 
        ADDR = (HOST, INFO_PORT)
        InfoSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        InfoSock.setsockopt(socket.socket.SOL_SOCKET, socket.socket.SO_REUSEADDR, 1)
        InfoSock.bind(ADDR)
        InfoSock.listen(5)  # Start server,waiting for client
        InfoSock, addr = InfoSock.accept()
        print('Info connected')
        while 1:
            try:
                info_data = ''
                info_data = str(InfoSock.recv(self.BUFSIZ).decode())
                info_get = info_data.split()
                self.CPU_TEP, self.CPU_USE, self.RAM_USE = info_get
                self.CPU_TEP_lab.config(text='CPU Temp: %s℃' % self.CPU_TEP)
                self.CPU_USE_lab.config(text='CPU Usage: %s' % self.CPU_USE)
                self.RAM_lab.config(text='RAM Usage: %s' % self.RAM_USE)
            except:
                pass

    def socket_connect(self):  # Call this function to connect with the server
        ip_adr = self.E1.get()
        if not ip_adr:
            ip_adr = self.num_import('IP:')
            self.l_ip_4.config(text='Connecting')
            self.l_ip_4.config(bg='#FF8F00')
            self.l_ip_5.config(text='Default:%s' % ip_adr)

        SERVER_IP = ip_adr
        SERVER_PORT = 10223
        BUFSIZ = 1024
        ADDR = (SERVER_IP, SERVER_PORT)
        self.tcpClicSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        for i in range(1, 6):
            if self.ip_stu == 1:
                try:
                    self.tcpClicSock.connect(ADDR)
                    self.l_ip_5.config(text='IP:%s' % ip_adr)
                    self.l_ip_4.config(text='Connected', bg='#558B2F')
                    self.replace_num('IP:', ip_adr)
                    self.E1.config(state='disabled')
                    self.ip_stu = 0

                    # Start all required threads
                    self.start_threads()
                    break
                except:
                    self.l_ip_4.config(text='Try %d/5 time(s)' % i, bg='#EF6C00')
                    self.ip_stu = 1
                    time.sleep(1)

        if self.ip_stu == 1:
            self.l_ip_4.config(text='Disconnected', bg='#F44336')

    def start_threads(self):
        threads = [
            (thread.Thread(target=self.connection_thread), True),
            (thread.Thread(target=self.video_thread), True),
            (thread.Thread(target=self.Info_receive), True),
            (thread.Thread(target=self.opencv_r), True)
        ]

        for t, daemon in threads:
            t.setDaemon(daemon)
            t.start()

    def connect(self, event=None):
        if self.ip_stu == 1:
            sc = thread.Thread(target=self.socket_connect)
            sc.setDaemon(True)
            sc.start()

    def connect_click(self):  # Call this function to connect with the server
        if self.ip_stu == 1:
            sc = thread.Thread(target=self.socket_connect)  # Define a thread for connection
            sc.setDaemon(True)  # 'True' means it is a front thread,it would close when the mainloop() closes
            sc.start()  # Thread starts

    def set_R(self, x):
        time.sleep(self.config["control"]["command_delay"])
        self.tcpClicSock.send(('wsR %s' % self.var_R.get()).encode())

    def set_G(self, x):
        time.sleep(self.config["control"]["command_delay"])
        self.tcpClicSock.send(('wsG %s' % self.var_G.get()).encode())

    def set_B(self, x):
        time.sleep(self.config["control"]["command_delay"])
        self.tcpClicSock.send(('wsB %s' % self.var_B.get()).encode())

    def EC_send(self, event):  # z
        self.tcpClicSock.send(('setEC %s' % self.var_ec.get()).encode())
        time.sleep(0.03)

    def EC_default(self, event):  # z
        self.var_ec.set(0)
        self.tcpClicSock.send(('defEC').encode())

    def scale_FL(self, x, y, w):  # 1
        def lip1_send(event):
            time.sleep(0.03)
            self.tcpClicSock.send(('lip1 %s' % self.var_lip1.get()).encode())

        def lip2_send(event):
            time.sleep(0.03)
            self.tcpClicSock.send(('lip2 %s' % self.var_lip2.get()).encode())

        def err_send(event):
            time.sleep(0.03)
            self.tcpClicSock.send(('err %s' % self.var_err.get()).encode())

        def call_Render(event):
            self.tcpClicSock.send(('Render').encode())

        def call_CVFL(event):
            self.tcpClicSock.send(('CVFL').encode())

        def call_WB(event):
            self.tcpClicSock.send(('WBswitch').encode())

        Scale_lip1 = tk.Scale(self.root, label=None,
                              from_=0, to=480, orient=tk.HORIZONTAL, length=w,
                              showvalue=1, tickinterval=None, resolution=1, variable=self.var_lip1,
                              troughcolor='#212121', command=lip1_send, fg=self.color_text, bg=self.color_bg,
                              highlightthickness=0)
        Scale_lip1.place(x=x, y=y)  # Define a Scale and put it in position

        Scale_lip2 = tk.Scale(self.root, label=None,
                              from_=0, to=480, orient=tk.HORIZONTAL, length=w,
                              showvalue=1, tickinterval=None, resolution=1, variable=self.var_lip2,
                              troughcolor='#212121', command=lip2_send, fg=self.color_text, bg=self.color_bg,
                              highlightthickness=0)
        Scale_lip2.place(x=x, y=y + 30)  # Define a Scale and put it in position

        Scale_err = tk.Scale(self.root, label=None,
                             from_=0, to=200, orient=tk.HORIZONTAL, length=w,
                             showvalue=1, tickinterval=None, resolution=1, variable=self.var_err, troughcolor='#212121',
                             command=err_send, fg=self.color_text, bg=self.color_bg, highlightthickness=0)
        Scale_err.place(x=x, y=y + 60)  # Define a Scale and put it in position

        canvas_cover = tk.Canvas(self.root, bg=self.color_bg, height=30, width=510, highlightthickness=0)
        canvas_cover.place(x=x, y=y + 90)

        Btn_Render = tk.Button(self.root, width=10, text='Render', fg=self.color_text, bg='#212121', relief='ridge')
        Btn_Render.place(x=x + w + 111, y=y + 20)
        Btn_Render.bind('<ButtonPress-1>', call_Render)

        self.Btn_CVFL = tk.Button(self.root, width=10, text='CV FL', fg=self.color_text, bg='#212121', relief='ridge')
        self.Btn_CVFL.place(x=x + w + 21, y=y + 20)
        self.Btn_CVFL.bind('<ButtonPress-1>', call_CVFL)

        Btn_WB = tk.Button(self.root, width=23, text='LineColorSwitch', fg=self.color_text, bg='#212121',
                           relief='ridge')
        Btn_WB.place(x=x + w + 21, y=y + 60)
        Btn_WB.bind('<ButtonPress-1>', call_WB)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title('Adeept RaspClaws')
        self.root.geometry('565x680')
        self.root.config(bg=self.color_bg)

        try:
            logo = tk.PhotoImage(file='logo.png')  # Define the picture of logo,but only supports '.png' and '.gif'
            l_logo = tk.Label(self.root, image=logo, bg=self.color_bg)  # Set a label to show the logo picture
            l_logo.place(x=30, y=13)  # Place the Label in a right position
        except:
            pass

        self.CPU_TEP_lab = tk.Label(self.root, width=18, text='CPU Temp:', fg=self.color_text, bg='#212121')
        self.CPU_TEP_lab.place(x=400, y=15)  # Define a Label and put it in position

        self.CPU_USE_lab = tk.Label(self.root, width=18, text='CPU Usage:', fg=self.color_text, bg='#212121')
        self.CPU_USE_lab.place(x=400, y=45)  # Define a Label and put it in position

        self.RAM_lab = tk.Label(self.root, width=18, text='RAM Usage:', fg=self.color_text, bg='#212121')
        self.RAM_lab.place(x=400, y=75)  # Define a Label and put it in position

        l_ip = tk.Label(self.root, width=18, text='Status', fg=self.color_text, bg=self.color_btn)
        l_ip.place(x=30, y=110)  # Define a Label and put it in position

        self.l_ip_4 = tk.Label(self.root, width=18, text='Disconnected', fg=self.color_text, bg='#F44336')
        self.l_ip_4.place(x=400, y=110)  # Define a Label and put it in position

        self.l_ip_5 = tk.Label(self.root, width=18, text='Use default IP', fg=self.color_text, bg=self.color_btn)
        self.l_ip_5.place(x=400, y=145)  # Define a Label and put it in position

        self.E1 = tk.Entry(self.root, show=None, width=16, bg="#37474F", fg='#eceff1')
        self.E1.place(x=180, y=40)  # Define a Entry and put it in position

        l_ip_3 = tk.Label(self.root, width=10, text='IP Address:', fg=self.color_text, bg='#000000')
        l_ip_3.place(x=175, y=15)  # Define a Label and put it in position

        label_openCV = tk.Label(self.root, width=28, text='OpenCV Status', fg=self.color_text, bg=self.color_btn)
        label_openCV.place(x=180, y=110)  # Define a Label and put it in position

        self.Btn_Smooth = tk.Button(self.root, width=8, text='Smooth', fg=self.color_text, bg=self.color_btn,
                                    relief='ridge')
        self.Btn_Smooth.place(x=240, y=230)
        self.Btn_Smooth.bind('<ButtonPress-1>', self.call_Smooth)
        self.root.bind('<KeyPress-f>', self.call_Smooth)

        self.Btn_Switch_1 = tk.Button(self.root, width=8, text='Port 1', fg=self.color_text, bg=self.color_btn,
                                      relief='ridge')
        self.Btn_Switch_2 = tk.Button(self.root, width=8, text='Port 2', fg=self.color_text, bg=self.color_btn,
                                      relief='ridge')
        self.Btn_Switch_3 = tk.Button(self.root, width=8, text='Port 3', fg=self.color_text, bg=self.color_btn,
                                      relief='ridge')

        self.Btn_Switch_1.place(x=30, y=265)
        self.Btn_Switch_2.place(x=100, y=265)
        self.Btn_Switch_3.place(x=170, y=265)

        self.Btn_Switch_1.bind('<ButtonPress-1>', self.call_Switch_1)
        self.Btn_Switch_2.bind('<ButtonPress-1>', self.call_Switch_2)
        self.Btn_Switch_3.bind('<ButtonPress-1>', self.call_Switch_3)

        Btn0 = tk.Button(self.root, width=8, text='Forward', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn1 = tk.Button(self.root, width=8, text='Backward', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn2 = tk.Button(self.root, width=8, text='Left', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn3 = tk.Button(self.root, width=8, text='Right', fg=self.color_text, bg=self.color_btn, relief='ridge')

        Btn_LeftSide = tk.Button(self.root, width=8, text='<--', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_LeftSide.place(x=30, y=195)
        Btn_LeftSide.bind('<ButtonPress-1>', self.call_LeftSide)
        Btn_LeftSide.bind('<ButtonRelease-1>', self.call_Turn_stop)

        Btn_RightSide = tk.Button(self.root, width=8, text='-->', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_RightSide.place(x=170, y=195)
        Btn_RightSide.bind('<ButtonPress-1>', self.call_RightSide)
        Btn_RightSide.bind('<ButtonRelease-1>', self.call_Turn_stop)

        Btn0.place(x=100, y=195)
        Btn1.place(x=100, y=230)
        Btn2.place(x=30, y=230)
        Btn3.place(x=170, y=230)

        Btn0.bind('<ButtonPress-1>', self.call_forward)
        Btn1.bind('<ButtonPress-1>', self.call_back)
        Btn2.bind('<ButtonPress-1>', self.call_Left)
        Btn3.bind('<ButtonPress-1>', self.call_Right)

        Btn0.bind('<ButtonRelease-1>', self.call_FB_stop)
        Btn1.bind('<ButtonRelease-1>', self.call_FB_stop)
        Btn2.bind('<ButtonRelease-1>', self.call_Turn_stop)
        Btn3.bind('<ButtonRelease-1>', self.call_Turn_stop)

        self.root.bind('<KeyPress-w>', self.call_forward)
        self.root.bind('<KeyPress-a>', self.call_Left)
        self.root.bind('<KeyPress-d>', self.call_Right)
        self.root.bind('<KeyPress-s>', self.call_back)

        self.root.bind('<KeyPress-q>', self.call_LeftSide)
        self.root.bind('<KeyPress-e>', self.call_RightSide)
        self.root.bind('<KeyRelease-q>', self.call_Turn_stop)
        self.root.bind('<KeyRelease-e>', self.call_Turn_stop)

        self.root.bind('<KeyRelease-w>', self.call_FB_stop)
        self.root.bind('<KeyRelease-a>', self.call_Turn_stop)
        self.root.bind('<KeyRelease-d>', self.call_Turn_stop)
        self.root.bind('<KeyRelease-s>', self.call_FB_stop)

        Btn_up = tk.Button(self.root, width=8, text='Up', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_down = tk.Button(self.root, width=8, text='Down', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_left = tk.Button(self.root, width=8, text='Left', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_right = tk.Button(self.root, width=8, text='Right', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_home = tk.Button(self.root, width=8, text='Home', fg=self.color_text, bg=self.color_btn, relief='ridge')
        Btn_up.place(x=400, y=195)
        Btn_down.place(x=400, y=265)
        Btn_left.place(x=330, y=230)
        Btn_right.place(x=470, y=230)
        Btn_home.place(x=400, y=230)
        self.root.bind('<KeyPress-i>', self.call_headup)
        self.root.bind('<KeyPress-k>', self.call_headdown)
        self.root.bind('<KeyPress-j>', self.call_headleft)
        self.root.bind('<KeyPress-l>', self.call_headright)
        self.root.bind('<KeyPress-h>', self.call_headhome)
        Btn_up.bind('<ButtonPress-1>', self.call_headup)
        Btn_down.bind('<ButtonPress-1>', self.call_headdown)
        Btn_left.bind('<ButtonPress-1>', self.call_headleft)
        Btn_right.bind('<ButtonPress-1>', self.call_headright)
        Btn_home.bind('<ButtonPress-1>', self.call_headhome)

        self.Btn14 = tk.Button(self.root, width=8, height=2, text='Connect', fg=self.color_text, bg=self.color_btn,
                               command=self.connect_click, relief='ridge')
        self.Btn14.place(x=315, y=15)  # Define a Button and put it in position

        self.root.bind('<Return>', self.connect)

        Scale_R = tk.Scale(self.root, label=None,
                           from_=0, to=255, orient=tk.HORIZONTAL, length=505,
                           showvalue=1, tickinterval=None, resolution=1, variable=self.var_R, troughcolor='#F44336',
                           command=self.set_R, fg=self.color_text, bg=self.color_bg, highlightthickness=0)
        Scale_R.place(x=30, y=330)  # Define a Scale and put it in position

        Scale_G = tk.Scale(self.root, label=None,
                           from_=0, to=255, orient=tk.HORIZONTAL, length=505,
                           showvalue=1, tickinterval=None, resolution=1, variable=self.var_G, troughcolor='#00E676',
                           command=self.set_G, fg=self.color_text, bg=self.color_bg, highlightthickness=0)
        Scale_G.place(x=30, y=360)  # Define a Scale and put it in position

        Scale_B = tk.Scale(self.root, label=None,
                           from_=0, to=255, orient=tk.HORIZONTAL, length=505,
                           showvalue=1, tickinterval=None, resolution=1, variable=self.var_B, troughcolor='#448AFF',
                           command=self.set_B, fg=self.color_text, bg=self.color_bg, highlightthickness=0)
        Scale_B.place(x=30, y=390)  # Define a Scale and put it in position

        Scale_ExpCom = tk.Scale(self.root, label='Exposure Compensation Level',
                                from_=-25, to=25, orient=tk.HORIZONTAL, length=315,
                                showvalue=1, tickinterval=None, resolution=1, variable=self.var_ec,
                                troughcolor='#212121', command=self.EC_send, fg=self.color_text, bg=self.color_bg,
                                highlightthickness=0)
        Scale_ExpCom.place(x=30, y=610)  # Define a Scale and put it in position

        canvas_cover_exp = tk.Canvas(self.root, bg=self.color_bg, height=30, width=510, highlightthickness=0)
        canvas_cover_exp.place(x=30, y=610 + 50)

        Btn_dEC = tk.Button(self.root, width=23, height=2, text='Set Default Exposure\nCompensation Level',
                            fg=self.color_text, bg='#212121', relief='ridge')
        Btn_dEC.place(x=30 + 315 + 21, y=610 + 3)
        Btn_dEC.bind('<ButtonPress-1>', self.EC_default)  # Z end

        canvas_cover = tk.Canvas(self.root, bg=self.color_bg, height=30, width=510, highlightthickness=0)
        canvas_cover.place(x=30, y=420)

        self.Btn_Steady = tk.Button(self.root, width=10, text='Steady', fg=self.color_text, bg=self.color_btn,
                                    relief='ridge')
        self.Btn_Steady.place(x=30, y=445)
        self.root.bind('<KeyPress-z>', self.call_steady)
        self.Btn_Steady.bind('<ButtonPress-1>', self.call_steady)

        self.Btn_FindColor = tk.Button(self.root, width=10, text='FindColor', fg=self.color_text, bg=self.color_btn,
                                       relief='ridge')
        self.Btn_FindColor.place(x=115, y=445)
        self.root.bind('<KeyPress-z>', self.call_FindColor)
        self.Btn_FindColor.bind('<ButtonPress-1>', self.call_FindColor)

        self.Btn_WatchDog = tk.Button(self.root, width=10, text='WatchDog', fg=self.color_text, bg=self.color_btn,
                                      relief='ridge')
        self.Btn_WatchDog.place(x=200, y=445)
        self.root.bind('<KeyPress-z>', self.call_WatchDog)
        self.Btn_WatchDog.bind('<ButtonPress-1>', self.call_WatchDog)

        self.Btn_Fun4 = tk.Button(self.root, width=10, text='Function 4', fg=self.color_text, bg=self.color_btn,
                                  relief='ridge')
        self.Btn_Fun4.place(x=285, y=445)
        self.root.bind('<KeyPress-z>', self.call_WatchDog)
        self.Btn_Fun4.bind('<ButtonPress-1>', self.call_WatchDog)

        self.Btn_Fun5 = tk.Button(self.root, width=10, text='Function 5', fg=self.color_text, bg=self.color_btn,
                                  relief='ridge')
        self.Btn_Fun5.place(x=370, y=445)
        self.root.bind('<KeyPress-z>', self.call_WatchDog)
        self.Btn_Fun5.bind('<ButtonPress-1>', self.call_WatchDog)

        self.Btn_Fun6 = tk.Button(self.root, width=10, text='Function 6', fg=self.color_text, bg=self.color_btn,
                                  relief='ridge')
        self.Btn_Fun6.place(x=455, y=445)
        self.root.bind('<KeyPress-z>', self.call_WatchDog)
        self.Btn_Fun6.bind('<ButtonPress-1>', self.call_WatchDog)

        self.scale_FL(30, 490, 315)  # 1

        # Add configuration button
        config_btn = tk.Button(self.root, width=10, text='Settings',
                               fg=self.config["colors"]["text"],
                               bg=self.config["colors"]["button"],
                               command=self.show_config_editor,
                               relief='ridge')
        config_btn.place(x=315, y=75)

        # Add Parameters button next to Settings
        self.show_params_btn = tk.Button(self.root, width=10, text='Parameters',
                                         fg=self.config["colors"]["text"],
                                         bg=self.config["colors"]["button"],
                                         command=self.show_parameter_panel,
                                         relief='ridge')
        self.show_params_btn.place(x=315, y=110)

    def show_parameter_panel(self):
        """Show the parameter control panel"""
        if not self.parameter_panel:
            from parameter_panel import ParameterPanel
            self.parameter_panel = ParameterPanel(self.root, callback=self.handle_parameter_change)
        else:
            self.parameter_panel.focus()  # Bring to front if already open

    def handle_parameter_change(self, param_name, value):
        """Handle parameter changes from the parameter panel"""
        try:
            if not self.tcpClicSock or not self.tcpClicSock.fileno() > 0:
                self.parameter_panel.status_var.set("Error: Not connected to server")
                return False

            # Format the parameter update command
            cmd = f'param_update {param_name} {value}'
            self.tcpClicSock.send(cmd.encode())

            # Wait for confirmation
            try:
                response = self.tcpClicSock.recv(1024).decode()
                if response == 'param_updated':
                    self.parameter_panel.status_var.set(f"Updated {param_name} successfully")
                    return True
                else:
                    self.parameter_panel.status_var.set(f"Error updating {param_name}")
                    return False
            except socket.socket.timeout:
                self.parameter_panel.status_var.set("Timeout waiting for server response")
                return False

        except Exception as e:
            self.parameter_panel.status_var.set(f"Error: {str(e)}")
            return False

    def setup_bindings(self):
        # Movement controls
        movement_bindings = {
            '<KeyPress-w>': self.call_forward,
            '<KeyPress-s>': self.call_back,
            '<KeyPress-a>': self.call_Left,
            '<KeyPress-d>': self.call_Right,
            '<KeyPress-q>': self.call_LeftSide,
            '<KeyPress-e>': self.call_RightSide,
            '<KeyRelease-w>': self.call_FB_stop,
            '<KeyRelease-s>': self.call_FB_stop,
            '<KeyRelease-a>': self.call_Turn_stop,
            '<KeyRelease-d>': self.call_Turn_stop,
            '<KeyRelease-q>': self.call_Turn_stop,
            '<KeyRelease-e>': self.call_Turn_stop
        }

        # Head movement controls
        head_bindings = {
            '<KeyPress-i>': self.call_headup,
            '<KeyPress-k>': self.call_headdown,
            '<KeyPress-j>': self.call_headleft,
            '<KeyPress-l>': self.call_headright,
            '<KeyPress-h>': self.call_headhome
        }

        # Function controls
        function_bindings = {
            '<KeyPress-z>': self.call_WatchDog,
            '<KeyPress-f>': self.call_Smooth,
            '<Return>': self.connect
        }

        # Apply all bindings
        for key, func in {**movement_bindings, **head_bindings, **function_bindings}.items():
            self.root.bind(key, func)

    def cleanup(self):
        """Ensure clean shutdown of all resources"""
        try:
            if self.tcpClicSock:
                self.tcpClicSock.close()
            if self.footage_socket:
                self.footage_socket.close()
            cv2.destroyAllWindows()
        except:
            pass
        finally:
            if self.root:
                self.root.quit()

    def start(self):
        """Start the GUI and handle cleanup on exit"""
        try:
            self.setup_gui()
            self.root.protocol("WM_DELETE_WINDOW", self.cleanup)  # Handle window close button
            self.root.mainloop()
        except Exception as e:
            print(f"Error in GUI: {e}")
            self.cleanup()
        finally:
            self.cleanup()


def main():
    controller = GUIController()
    try:
        controller.start()
    except:
        controller.cleanup()


if __name__ == '__main__':
    main()
