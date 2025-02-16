"""HTML templates for the RaspClaws web interface"""

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>RaspClaws Control</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <h1>RaspClaws Control</h1>
    
    <div class="control-group">
        <h2>Hop Controls</h2>
        <div class="control-row">
            <label for="hopSpeed">Speed (1-100):</label>
            <input type="range" id="hopSpeed" class="slider" min="1" max="100" value="20">
            <span id="speedValue">20</span>
        </div>
        
        <div class="control-row">
            <label for="airTime">Air Time (0.1-1.0s):</label>
            <input type="range" id="airTime" class="slider" min="1" max="10" value="3">
            <span id="airTimeValue">0.3</span>
        </div>
        
        <button onclick="sendHop()" class="control-button">Hop!</button>
    </div>

    <div class="control-group">
        <h2>Light Controls</h2>
        <div class="light-control">
            <label for="brightness">Brightness:</label>
            <input type="range" id="brightness" class="slider" min="0" max="255" value="255">
            <span id="brightnessValue">255</span>
        </div>
        
        <div class="light-control">
            <label>Color:</label>
            <input type="color" id="colorPicker" value="#0000ff">
            <button onclick="setColor()" class="control-button">Set Color</button>
        </div>
        
        <div class="light-control">
            <label>Patterns:</label>
            <div class="button-group">
                <button onclick="setPattern('rainbow')" class="pattern-button">Rainbow</button>
                <button onclick="setPattern('pulse')" class="pattern-button">Pulse</button>
                <button onclick="setPattern('breath')" class="pattern-button">Breath</button>
                <button onclick="setPattern('none')" class="pattern-button">Off</button>
            </div>
        </div>
    </div>

    <div id="status" class="status-panel">
        <h2>System Status</h2>
        <div id="sensorData">Initializing sensors...</div>
        <div id="connectionStatus">Checking connection...</div>
    </div>

    <script src="/static/main.js"></script>
</body>
</html>
'''

PARAMETERS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>RaspClaws Parameters</title>
    <link rel="stylesheet" href="/static/parameters.css">
</head>
<body>
    <h1>RaspClaws Parameter Control</h1>
    
    <div class="monitor">
        <div class="monitor-item">
            <strong>Kalman Filter X:</strong> <span id="kalman_x">--</span>
        </div>
        <div class="monitor-item">
            <strong>Kalman Filter Y:</strong> <span id="kalman_y">--</span>
        </div>
        <div class="monitor-item">
            <strong>PID Status:</strong> <span id="pid_status">--</span>
        </div>
        <div class="monitor-item">
            <strong>Stability:</strong> <span id="stability">--</span>%
        </div>
    </div>

    <div class="param-sections">
        <div class="param-group">
            <h3>Kalman Filter</h3>
            <div class="param-row">
                <label>Process Noise (Q)</label>
                <input type="range" class="param-slider" 
                       min="0.001" max="1" step="0.001" value="0.01"
                       oninput="updateParam('Q', this.value)">
                <span class="param-value">0.01</span>
            </div>
            <div class="param-row">
                <label>Measurement Noise (R)</label>
                <input type="range" class="param-slider" 
                       min="0.01" max="1" step="0.01" value="0.1"
                       oninput="updateParam('R', this.value)">
                <span class="param-value">0.1</span>
            </div>
        </div>

        <div class="param-group">
            <h3>PID Control</h3>
            <div class="param-row">
                <label>P Gain</label>
                <input type="range" class="param-slider" 
                       min="0" max="10" step="0.1" value="5"
                       oninput="updateParam('P', this.value)">
                <span class="param-value">5.0</span>
            </div>
            <div class="param-row">
                <label>I Gain</label>
                <input type="range" class="param-slider" 
                       min="0" max="1" step="0.001" value="0.01"
                       oninput="updateParam('I', this.value)">
                <span class="param-value">0.01</span>
            </div>
            <div class="param-row">
                <label>D Gain</label>
                <input type="range" class="param-slider" 
                       min="0" max="1" step="0.001" value="0"
                       oninput="updateParam('D', this.value)">
                <span class="param-value">0.0</span>
            </div>
        </div>

        <div class="param-group">
            <h3>Movement</h3>
            <div class="param-row">
                <label>Speed Scale</label>
                <input type="range" class="param-slider" 
                       min="0.1" max="2" step="0.1" value="1"
                       oninput="updateParam('speed_scale', this.value)">
                <span class="param-value">1.0</span>
            </div>
            <div class="param-row">
                <label>Movement Smoothing</label>
                <input type="range" class="param-slider" 
                       min="0" max="1" step="0.01" value="0.5"
                       oninput="updateParam('smoothing', this.value)">
                <span class="param-value">0.5</span>
            </div>
        </div>
    </div>

    <div id="notification" class="notification"></div>

    <script src="/static/parameters.js"></script>
</body>
</html>
'''