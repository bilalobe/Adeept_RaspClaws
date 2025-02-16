#!/usr/bin/python
# -*- coding: UTF-8 -*-
# File name   : client.py
# Description : client  
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William
# Date        : 2018/08/22
import base64
import socket
import threading as thread
import time
import tkinter as tk
from typing_extensions import runtime

import cv2
import numpy as np
import zmq


def info_receive():
    """
    Thread to receive system info.
    """
    global CPU_TEP, CPU_USE, RAM_USE, InfoSock
    HOST = ''
    INFO_PORT = 2256  # Define port serial 
    ADDR = (HOST, INFO_PORT)
    InfoSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    InfoSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    InfoSock.bind(ADDR)
    InfoSock.listen(5)  # Start server, waiting for client
    
    connection, _ = InfoSock.accept()  # Use _ to ignore unused addr
    InfoSock = connection  # Reassign InfoSock to the connected socket
    print('Info connected')
    
    while True:
        try:
            data = InfoSock.recv(1024)
            if not data:
                break
            CPU_TEP, CPU_USE, RAM_USE = data.decode().split(',')
        except socket.error as e:
            print(f"Socket error: {e}")
            break
        except Exception as e:
            print(f"Error receiving system info: {e}")
            time.sleep(1)
            continue


class RaspClawsClient:
    def __init__(self):
        self.ip_stu = 1  # Shows connection status
        self.c_f_stu = 0
        self.c_b_stu = 0
        self.c_l_stu = 0
        self.c_r_stu = 0
        self.c_ls_stu = 0
        self.c_rs_stu = 0
        self.funcMode = 0
        self.tcpClicSock = ''
        self.root = tk.Tk()
        self.stat = 0

        self.CPU_TEP_lab = tk.Label(self.root, text="CPU Temp:")
        self.CPU_TEP_lab.pack()
        self.CPU_USE_lab = tk.Label(self.root, text="CPU Usage:")
        self.CPU_USE_lab.pack()
        self.RAM_lab = tk.Label(self.root, text="RAM Usage:")
        self.RAM_lab.pack()

        self.l_ip_4 = tk.Label(self.root, text="Status")
        self.l_ip_4.pack()
        self.l_ip_5 = tk.Label(self.root, text="IP Info")
        self.l_ip_5.pack()
        self.E1 = tk.Entry(self.root)
        self.E1.pack()
        self.Btn14 = tk.Button(self.root, text="Connect", command=self.connect)
        self.Btn14.pack()

        # Define default colors for buttons
        self.color_btn = "#EEEEEE"
        self.color_text = "#000000"

        # Initialize button variables with dummy tkinter buttons
        self.Btn_Steady = tk.Button(text="Steady")
        self.Btn_FindColor = tk.Button(text="FindColor")
        self.Btn_WatchDog = tk.Button(text="WatchDog")
        self.Btn_Fun4 = tk.Button(text="Fun4")
        self.Btn_Fun5 = tk.Button(text="Fun5")
        self.Btn_Fun6 = tk.Button(text="Fun6")
        self.Btn_Smooth = tk.Button(text="Smooth")
        self.Btn_Switch_3 = tk.Button(text="Switch 3")
        self.Btn_Switch_2 = tk.Button(text="Switch 2")
        self.Btn_Switch_1 = tk.Button(text="Switch 1")

        self.Switch_3 = 0
        self.Switch_2 = 0
        self.Switch_1 = 0
        self.SmoothMode = 0

        self.setup_threads()

    def setup_threads(self):
        fps_threading = thread.Thread(target=self.get_fps)
        fps_threading.daemon = True
        fps_threading.start()

        video_threading = thread.Thread(target=self.video_thread)
        video_threading.daemon = True
        video_threading.start()

    def video_thread(self):
        """
        Thread to handle video streaming.
        """
        global footage_socket, font, frame_num, fps
        context = zmq.Context()
        footage_socket = context.socket(zmq.SUB)
        footage_socket.bind('tcp://*:5555')
        footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))

        font = cv2.FONT_HERSHEY_SIMPLEX

        frame_num = 0
        fps = 0

    def get_fps(self):
        """
        Thread to calculate FPS.
        """
        global frame_num, fps
        while True:
            try:
                data = InfoSock.recv(1024)
                if not data:
                    break
                CPU_TEP, CPU_USE, RAM_USE = data.decode().split(',')
                time.sleep(1)
            except Exception as e:
                print(f"Error receiving system info: {e}")
                time.sleep(1)
                fps = frame_num
                frame_num = 0

    def opencv_r(self):
        """
        Thread to handle OpenCV processing.
        """
        global frame_num
        while True:
            try:
                frame = footage_socket.recv_string()
                img = base64.b64decode(frame)
                npimg = np.frombuffer(img, dtype=np.uint8)
                source = cv2.imdecode(npimg, 1)
                cv2.putText(source, f'PC FPS: {fps}', (40, 20), font, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                try:
                    cv2.putText(source, f'CPU Temperature: {CPU_TEP}', (370, 350), font, 0.5, (128, 255, 128), 1,
                                cv2.LINE_AA)
                    cv2.putText(source, f'CPU Usage: {CPU_USE}', (370, 380), font, 0.5, (128, 255, 128), 1, cv2.LINE_AA)
                    cv2.putText(source, f'RAM Usage: {RAM_USE}', (370, 410), font, 0.5, (128, 255, 128), 1, cv2.LINE_AA)
                except Exception as e:
                    print(f"Error displaying system info: {e}")
                cv2.imshow("Stream", source)
                frame_num += 1
                cv2.waitKey(1)
            except Exception as e:
                print(f"Error in OpenCV processing: {e}")
                time.sleep(0.5)
                break

    def replace_num(self, initial, new_num):
        """
        Replace a number in the IP configuration file.
        """
        new_line = ""
        str_num = str(new_num)
        try:
            with open("./ip.txt", "r") as file:
                for line in file.readlines():
                    if line.startswith(initial):
                        line = initial + str_num
                    new_line += line
            with open("./ip.txt", "w") as file:
                file.writelines(new_line)
        except FileNotFoundError:
            print("Error: IP configuration file not found.")
        except Exception as error:
            print(f"Error writing to IP configuration file: {error}")

    def num_import(self, initial):
        """
        Import a number from the IP configuration file.
        """
        try:
            with open("./ip.txt", "r") as file:
                for line in file.readlines():
                    if line.startswith(initial):
                        return line[len(initial):].strip()
        except FileNotFoundError:
            print("Error: IP configuration file not found.")
        except Exception as error:
            print(f"Error reading from IP configuration file: {error}")
        return None

    def read_ip_config(self):
        """
        Read the IP address from configuration using num_import helper function.
        """
        return self.num_import('IP:')

    def connect_to_server(self, host, port):
        """
        Connect to the server using a context manager.
        Returns the socket object if successful, or None otherwise.
        """
        try:
            with socket.create_connection((host, port)) as sock:
                # Process the connection
                self.process_connection(sock)
                return sock
        except socket.error as error:
            print(f"Socket connection error: {error}")
        return None

    def process_connection(self, sock):
        """
        Example function to demonstrate processing a socket connection.
        """
        # Clear and descriptive variable names for data
        data_received = sock.recv(1024)
        print(f"Data received: {data_received.decode()}")

    def call_forward(self, event):
        """
        Command the car to move forward.
        """
        if self.c_f_stu == 0:
            self.tcpClicSock.send('forward'.encode())
            self.c_f_stu = 1

    def call_back(self, event):
        """
        Command the car to move backward.
        """
        if self.c_b_stu == 0:
            self.tcpClicSock.send('backward'.encode())
            self.c_b_stu = 1

    def call_fb_stop(self, event):
        """
        Command the car to stop moving.
        """
        self.c_f_stu = 0
        self.c_b_stu = 0
        self.tcpClicSock.send('DS'.encode())

    def call_turn_stop(self, event):
        """
        Command the car to stop turning.
        """
        self.c_l_stu = 0
        self.c_r_stu = 0
        self.c_ls_stu = 0
        self.c_rs_stu = 0
        self.tcpClicSock.send('TS'.encode())

    def call_left(self, event):
        """
        Command the car to turn left.
        """
        if self.c_l_stu == 0:
            self.tcpClicSock.send('left'.encode())
            self.c_l_stu = 1

    def call_right(self, event):
        """
        Command the car to turn right.
        """
        if self.c_r_stu == 0:
            self.tcpClicSock.send('right'.encode())
            self.c_r_stu = 1

    def call_leftside(self, event):
        """
        Command the car to move left side.
        """
        if self.c_ls_stu == 0:
            self.tcpClicSock.send('leftside'.encode())
            self.c_ls_stu = 1

    def call_rightside(self, event):
        """
        Command the car to move right side.
        """
        if self.c_rs_stu == 0:
            self.tcpClicSock.send('rightside'.encode())
            self.c_rs_stu = 1

    def call_headup(self, event):
        """
        Command the car to move head up.
        """
        self.tcpClicSock.send('headup'.encode())

    def call_headdown(self, event):
        """
        Command the car to move head down.
        """
        self.tcpClicSock.send('headdown'.encode())

    def call_headleft(self, event):
        """
        Command the car to move head left.
        """
        self.tcpClicSock.send('headleft'.encode())

    def call_headright(self, event):
        """
        Command the car to move head right.
        """
        self.tcpClicSock.send('headright'.encode())

    def call_headhome(self, event):
        """
        Command the car to move head home.
        """
        self.tcpClicSock.send('headhome'.encode())

    def call_steady(self, event):
        """
        Command the car to steady.
        """
        if self.funcMode == 0:
            self.tcpClicSock.send('steady'.encode())
        else:
            self.tcpClicSock.send('funEnd'.encode())

    def call_findcolor(self, event):
        """
        Command the car to find color.
        """
        if self.funcMode == 0:
            self.tcpClicSock.send('FindColor'.encode())
        else:
            self.tcpClicSock.send('funEnd'.encode())

    def call_watchdog(self, event):
        """
        Command the car to watch dog.
        """
        if self.funcMode == 0:
            self.tcpClicSock.send('WatchDog'.encode())
        else:
            self.tcpClicSock.send('funEnd'.encode())

    def call_smooth(self, event):
        """
        Command the car to smooth.
        """
        if self.SmoothMode == 0:
            self.tcpClicSock.send('Smooth_on'.encode())
        else:
            self.tcpClicSock.send('Smooth_off'.encode())

    def call_switch_1(self, event):
        """
        Command the car to switch 1.
        """
        if self.Switch_1 == 0:
            self.tcpClicSock.send('Switch_1_on'.encode())
        else:
            self.tcpClicSock.send('Switch_1_off'.encode())

    def call_switch_2(self, event):
        """
        Command the car to switch 2.
        """
        if self.Switch_2 == 0:
            self.tcpClicSock.send('Switch_2_on'.encode())
        else:
            self.tcpClicSock.send('Switch_2_off'.encode())

    def call_switch_3(self, event):
        """
        Command the car to switch 3.
        """
        if self.Switch_3 == 0:
            self.tcpClicSock.send('Switch_3_on'.encode())
        else:
            self.tcpClicSock.send('Switch_3_off'.encode())

    def all_btn_red(self):
        """
        Set all buttons to red.
        """
        self.Btn_Steady.config(bg='#FF6D00', fg='#000000')
        self.Btn_FindColor.config(bg='#FF6D00', fg='#000000')
        self.Btn_WatchDog.config(bg='#FF6D00', fg='#000000')
        self.Btn_Fun4.config(bg='#FF6D00', fg='#000000')
        self.Btn_Fun5.config(bg='#FF6D00', fg='#000000')
        self.Btn_Fun6.config(bg='#FF6D00', fg='#000000')

    def all_btn_normal(self):
        """
        Set all buttons to normal color.
        """
        self.Btn_Steady.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_FindColor.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_WatchDog.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_Fun4.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_Fun5.config(bg=self.color_btn, fg=self.color_text)
        self.Btn_Fun6.config(bg=self.color_btn, fg=self.color_text)

    def connection_thread(self):
        """
        Thread to handle connection.
        """
        while True:
            car_info = (self.tcpClicSock.recv(BUFSIZ)).decode()
            if not car_info:
                continue

            elif 'FindColor' in car_info:
                self.funcMode = 1
                self.all_btn_red()
                self.Btn_FindColor.config(bg='#00E676')

            elif 'steady' in car_info:
                self.funcMode = 1
                self.all_btn_red()
                self.Btn_Steady.config(bg='#00E676')

            elif 'WatchDog' in car_info:
                self.funcMode = 1
                self.all_btn_red()
                self.Btn_WatchDog.config(bg='#00E676')

            elif 'Smooth_on' in car_info:
                self.SmoothMode = 1
                self.Btn_Smooth.config(bg='#4CAF50')

            elif 'Smooth_off' in car_info:
                self.SmoothMode = 0
                self.Btn_Smooth.config(bg=self.color_btn)

            elif 'Switch_3_on' in car_info:
                self.Switch_3 = 1
                self.Btn_Switch_3.config(bg='#4CAF50')

            elif 'Switch_2_on' in car_info:
                self.Switch_2 = 1
                self.Btn_Switch_2.config(bg='#4CAF50')

            elif 'Switch_1_on' in car_info:
                self.Switch_1 = 1
                self.Btn_Switch_1.config(bg='#4CAF50')

            elif 'Switch_3_off' in car_info:
                self.Switch_3 = 0
                self.Btn_Switch_3.config(bg=self.color_btn)

            elif 'Switch_2_off' in car_info:
                self.Switch_2 = 0
                self.Btn_Switch_2.config(bg=self.color_btn)

            elif 'Switch_1_off' in car_info:
                self.Switch_1 = 0
                self.Btn_Switch_1.config(bg=self.color_btn)

            elif 'FunEnd' in car_info:
                self.funcMode = 0
                self.all_btn_normal()

            print(car_info)

    def socket_connect(self):
        """
        Call this function to connect with the server.
        """
        global ADDR, BUFSIZ, ipaddr
        ip_adr = self.E1.get()  # Get the IP address from Entry

        if ip_adr == '':  # If no input IP address in Entry, import a default IP
            ip_adr = self.num_import('IP:')
            self.l_ip_4.config(text='Connecting')
            self.l_ip_4.config(bg='#FF8F00')
            self.l_ip_5.config(text=f'Default: {ip_adr}')

        SERVER_IP = ip_adr
        SERVER_PORT = 10223  # Define port serial 
        BUFSIZ = 1024  # Define buffer size
        ADDR = (SERVER_IP, SERVER_PORT)
        self.tcpClicSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Set connection value for socket

        for i in range(1, 6):  # Try 5 times if disconnected
            if self.ip_stu == 1:
                print(f"Connecting to server @ {SERVER_IP}:{SERVER_PORT}...")
                print("Connecting")
                self.tcpClicSock.connect(ADDR)  # Connection with the server

                print("Connected")

                self.l_ip_5.config(text=f'IP: {ip_adr}')
                self.l_ip_4.config(text='Connected')
                self.l_ip_4.config(bg='#558B2F')

                self.replace_num('IP:', ip_adr)
                self.E1.config(state='disabled')  # Disable the Entry
                self.Btn14.config(state='disabled')  # Disable the Entry

                self.ip_stu = 0  # '0' means connected

                connection_threading = thread.Thread(
                    target=self.connection_thread)  # Define a thread for FPV and OpenCV
                connection_threading.daemon = True  # 'True' means it is a front thread, it would close when the mainloop() closes
                connection_threading.start()  # Thread starts

                info_threading = thread.Thread(target=info_receive)  # Define a thread for FPV and OpenCV
                info_threading.daemon = True  # 'True' means it is a front thread, it would close when the mainloop() closes
                info_threading.start()  # Thread starts

                video_threading = thread.Thread(target=self.opencv_r)  # Define a thread for FPV and OpenCV
                video_threading.daemon = True  # 'True' means it is a front thread, it would close when the mainloop() closes
                video_threading.start()  # Thread starts

                break
            else:
                print("Cannot connect to server, try it later!")
                self.l_ip_4.config(text=f'Try {i}/5 time(s)')
                self.l_ip_4.config(bg='#EF6C00')
                print(f'Try {i}/5 time(s)')
                self.ip_stu = 1
                time.sleep(1)
                continue

        if self.ip_stu == 1:
            self.l_ip_4.config(text='Disconnected')
            self.l_ip_4.config(bg='#F44336')
            self.l_ip_4.config(bg='#EF6C00')
            print(f'Try {i}/5 time(s)')
            self.ip_stu = 1
            time.sleep(1)

    def connect(self, event):
        """
        Call this function to connect with the server.
        """
        if self.ip_stu == 1:
            sc = thread.Thread(target=self.socket_connect)  # Define a thread for connection
            sc.daemon = True  # 'True' means it is a front thread, it would close when the mainloop() closes
            sc.start()  # Thread starts

    def connect_click(self):
        """
        Call this function to connect with the server.
        """
        try:
            ip_address = self.read_ip_config()
            if ip_address is None:
                raise RuntimeError("IP address could not be loaded.")

            sock = self.connect_to_server(ip_address, 8080)
            if sock is None:
                raise RuntimeError("Failed to connect to the server.")
        except Exception as e:
            print(f"Connection failed: {e}")
            raise runtime


if __name__ == "__main__":
    client = RaspClawsClient()
    client.root.mainloop()
