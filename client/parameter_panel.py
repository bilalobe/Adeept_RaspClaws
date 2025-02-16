import json
import tkinter
from tkinter import ttk


class ParameterPanel(tkinter.Toplevel):
    """
    """
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.title("Parameter Control Panel")
        self.geometry("600x800")

        self.callback = callback
        self.changes = {}

        # Add monitoring display
        self.create_monitoring_display()

        # Add status bar
        self.status_var = tkinter.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var)
        self.status_bar.pack(side=tkinter.BOTTOM, fill=tkinter.X, padx=5, pady=2)

        # Initialize monitors
        self.monitors = {}

        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Create tabs
        self.kalman_tab = self.create_tab("Kalman Filter")
        self.pid_tab = self.create_tab("PID Control")
        self.movement_tab = self.create_tab("Movement")
        self.balance_tab = self.create_tab("Balance")

        self.setup_kalman_controls()
        self.setup_pid_controls()
        self.setup_movement_controls()
        self.setup_balance_controls()

        # Create control buttons
        self.create_control_buttons()

        self.load_saved_parameters()

    def create_tab(self, name):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=name)
        return tab

    def create_slider(self, parent, name, from_, to_, resolution, default, row):
        """Create a labeled slider with value display"""
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky='ew', padx=5, pady=2)

        label = ttk.Label(frame, text=name)
        label.pack(side=tkinter.LEFT)

        value_label = ttk.Label(frame, width=8)
        value_label.pack(side=tkinter.RIGHT)

        slider = ttk.Scale(frame, from_=from_, to=to_, orient=tkinter.HORIZONTAL)
        slider.set(default)
        slider.pack(side=tkinter.RIGHT, fill=tkinter.X, expand=True, padx=5)

        def update_value(event=None):
            value_label.config(text=f"{slider.get():.3f}")
            self.parameter_changed(name, slider.get())

        slider.config(command=update_value)
        update_value()

        return slider

    def setup_kalman_controls(self):
        """Setup Kalman filter parameter controls"""
        params = [
            ("Process Noise (Q)", 0.001, 1.0, 0.001, 0.01),
            ("Measurement Noise (R)", 0.01, 1.0, 0.001, 0.1),
            ("Innovation Alpha", 0.0, 1.0, 0.01, 0.01),
            ("History Window", 10, 100, 1, 50),
        ]

        for i, (name, min_, max_, res, default) in enumerate(params):
            self.create_slider(self.kalman_tab, name, min_, max_, res, default, i)

    def setup_pid_controls(self):
        """Setup PID controller parameter controls"""
        params = [
            ("P Gain", 0.0, 10.0, 0.1, 5.0),
            ("I Gain", 0.0, 1.0, 0.001, 0.01),
            ("D Gain", 0.0, 1.0, 0.001, 0.0),
            ("Windup Guard", 0.0, 100.0, 1.0, 20.0),
        ]

        for i, (name, min_, max_, res, default) in enumerate(params):
            self.create_slider(self.pid_tab, name, min_, max_, res, default, i)

    def setup_movement_controls(self):
        """Setup movement parameter controls"""
        params = [
            ("Speed Scale", 0.1, 2.0, 0.1, 1.0),
            ("Turn Scale", 0.1, 2.0, 0.1, 1.0),
            ("Step Size", 1, 10, 1, 5),
            ("Movement Smoothing", 0.0, 1.0, 0.01, 0.5),
        ]

        for i, (name, min_, max_, res, default) in enumerate(params):
            self.create_slider(self.movement_tab, name, min_, max_, res, default, i)

    def setup_balance_controls(self):
        """Setup balance parameter controls"""
        params = [
            ("X Balance Target", -10.0, 10.0, 0.1, 0.0),
            ("Y Balance Target", -10.0, 10.0, 0.1, 0.0),
            ("Balance Sensitivity", 0.1, 2.0, 0.1, 1.0),
            ("Stability Threshold", 0.1, 5.0, 0.1, 1.0),
        ]

        for i, (name, min_, max_, res, default) in enumerate(params):
            self.create_slider(self.balance_tab, name, min_, max_, res, default, i)

    def create_control_buttons(self):
        """Create control buttons at the bottom"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tkinter.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Apply", command=self.apply_changes).pack(side=tkinter.RIGHT, padx=5)
        ttk.Button(button_frame, text="Save", command=self.save_parameters).pack(side=tkinter.RIGHT, padx=5)
        ttk.Button(button_frame, text="Load", command=self.load_saved_parameters).pack(side=tkinter.RIGHT, padx=5)
        ttk.Button(button_frame, text="Reset", command=self.reset_parameters).pack(side=tkinter.RIGHT, padx=5)

    def parameter_changed(self, name, value):
        """Called when a parameter value changes"""
        self.changes[name] = value
        if self.callback:
            self.callback(name, value)

    def apply_changes(self):
        """Apply all pending changes"""
        if self.callback:
            for name, value in self.changes.items():
                self.callback(name, value)
        self.changes.clear()

    def save_parameters(self):
        """Save current parameters to file"""
        params = {
            'kalman': {
                'Q': self.changes.get('Process Noise (Q)', 0.01),
                'R': self.changes.get('Measurement Noise (R)', 0.1),
                'alpha': self.changes.get('Innovation Alpha', 0.01),
                'history': self.changes.get('History Window', 50)
            },
            'pid': {
                'P': self.changes.get('P Gain', 5.0),
                'I': self.changes.get('I Gain', 0.01),
                'D': self.changes.get('D Gain', 0.0),
                'windup': self.changes.get('Windup Guard', 20.0)
            },
            'movement': {
                'speed_scale': self.changes.get('Speed Scale', 1.0),
                'turn_scale': self.changes.get('Turn Scale', 1.0),
                'step_size': self.changes.get('Step Size', 5),
                'smoothing': self.changes.get('Movement Smoothing', 0.5)
            },
            'balance': {
                'x_target': self.changes.get('X Balance Target', 0.0),
                'y_target': self.changes.get('Y Balance Target', 0.0),
                'sensitivity': self.changes.get('Balance Sensitivity', 1.0),
                'threshold': self.changes.get('Stability Threshold', 1.0)
            }
        }

        with open('parameters.json', 'w') as f:
            json.dump(params, f, indent=4)

    def load_saved_parameters(self):
        """Load parameters from file"""
        try:
            with open('parameters.json', 'r') as f:
                params = json.load(f)

            # Update all controls with loaded values
            for tab_name, tab_params in params.items():
                for param_name, value in tab_params.items():
                    self.parameter_changed(param_name, value)

        except FileNotFoundError:
            pass  # Use defaults if file doesn't exist

    def reset_parameters(self):
        """Reset all parameters to defaults"""
        self.changes.clear()
        self.load_saved_parameters()

    def create_monitoring_display(self):
        """Create monitoring display frame"""
        self.monitor_frame = ttk.LabelFrame(self, text="Real-time Monitoring")
        self.monitor_frame.pack(fill=tkinter.X, padx=5, pady=5, before=self.notebook)

        # Create grid of monitoring values
        self.monitors = {}

        # Kalman filter stats
        row = 0
        ttk.Label(self.monitor_frame, text="Kalman X:").grid(row=row, column=0, padx=5)
        self.monitors['kalman_x'] = ttk.Label(self.monitor_frame, text="--")
        self.monitors['kalman_x'].grid(row=row, column=1, padx=5)

        ttk.Label(self.monitor_frame, text="Kalman Y:").grid(row=row, column=2, padx=5)
        self.monitors['kalman_y'] = ttk.Label(self.monitor_frame, text="--")
        self.monitors['kalman_y'].grid(row=row, column=3, padx=5)

        # PID outputs
        row += 1
        ttk.Label(self.monitor_frame, text="PID X:").grid(row=row, column=0, padx=5)
        self.monitors['pid_x'] = ttk.Label(self.monitor_frame, text="--")
        self.monitors['pid_x'].grid(row=row, column=1, padx=5)

        ttk.Label(self.monitor_frame, text="PID Y:").grid(row=row, column=2, padx=5)
        self.monitors['pid_y'] = ttk.Label(self.monitor_frame, text="--")
        self.monitors['pid_y'].grid(row=row, column=3, padx=5)

        # Balance stats
        row += 1
        ttk.Label(self.monitor_frame, text="Balance Error:").grid(row=row, column=0, padx=5)
        self.monitors['balance_error'] = ttk.Label(self.monitor_frame, text="--")
        self.monitors['balance_error'].grid(row=row, column=1, padx=5)

        ttk.Label(self.monitor_frame, text="Stability:").grid(row=row, column=2, padx=5)
        self.monitors['stability'] = ttk.Label(self.monitor_frame, text="--")
        self.monitors['stability'].grid(row=row, column=3, padx=5)

        # Start monitoring update loop
        self.after(100, self.update_monitors)

    def update_monitors(self):
        """Update monitoring displays with latest values"""
        if self.callback:
            values = self.callback('get_monitor_values', None)
            if values:
                for key, value in values.items():
                    if key in self.monitors:
                        if isinstance(value, float):
                            self.monitors[key].config(text=f"{value:.3f}")
                        else:
                            self.monitors[key].config(text=str(value))

        # Schedule next update
        self.after(100, self.update_monitors)
