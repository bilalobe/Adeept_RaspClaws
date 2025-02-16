// Main control interface functionality
const speedSlider = document.getElementById('hopSpeed');
const speedValue = document.getElementById('speedValue');
const airTimeSlider = document.getElementById('airTime');
const airTimeValue = document.getElementById('airTimeValue');
const brightnessSlider = document.getElementById('brightness');
const brightnessValue = document.getElementById('brightnessValue');

// Update display values on slider change
speedSlider.addEventListener('input', () => {
    speedValue.textContent = speedSlider.value;
});

airTimeSlider.addEventListener('input', () => {
    airTimeValue.textContent = (airTimeSlider.value / 10).toFixed(1);
});

brightnessSlider.addEventListener('input', () => {
    brightnessValue.textContent = brightnessSlider.value;
    setBrightness(brightnessSlider.value);
});

// API calls
async function sendHop() {
    const speed = speedSlider.value;
    const airTime = airTimeSlider.value / 10;
    
    try {
        const response = await fetch('/hop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ speed, air_time: airTime })
        });
        
        if (!response.ok) throw new Error('Hop command failed');
        
        showNotification('Hop executed successfully', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification('Hop failed: ' + error.message, 'error');
    }
}

async function setBrightness(value) {
    try {
        const response = await fetch('/lights/brightness', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({brightness: parseInt(value)})
        });
        
        if (!response.ok) throw new Error('Failed to set brightness');
    } catch (error) {
        console.error('Error setting brightness:', error);
        showNotification('Failed to set brightness', 'error');
    }
}

async function setColor() {
    const color = document.getElementById('colorPicker').value;
    const r = parseInt(color.substr(1,2), 16);
    const g = parseInt(color.substr(3,2), 16);
    const b = parseInt(color.substr(5,2), 16);
    
    try {
        const response = await fetch('/lights/color', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({r, g, b})
        });
        
        if (!response.ok) throw new Error('Failed to set color');
        showNotification('Color updated', 'success');
    } catch (error) {
        console.error('Error setting color:', error);
        showNotification('Failed to set color', 'error');
    }
}

async function setPattern(pattern) {
    try {
        const response = await fetch('/lights/pattern', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({pattern})
        });
        
        if (!response.ok) throw new Error('Failed to set pattern');
        showNotification(`Pattern ${pattern} activated`, 'success');
    } catch (error) {
        console.error('Error setting pattern:', error);
        showNotification('Failed to set pattern', 'error');
    }
}

// Update sensor data periodically
async function updateSensorStatus() {
    try {
        const response = await fetch('/hop/status');
        const data = await response.json();
        
        const sensorDiv = document.getElementById('sensorData');
        const connectionDiv = document.getElementById('connectionStatus');
        
        if (data.connected) {
            sensorDiv.innerHTML = `
                X: ${data.x.toFixed(2)} (raw: ${data.raw_x.toFixed(2)})<br>
                Y: ${data.y.toFixed(2)} (raw: ${data.raw_y.toFixed(2)})
            `;
            connectionDiv.innerHTML = '<span class="status-ok">Connected</span>';
        } else {
            sensorDiv.textContent = 'No sensor data available';
            connectionDiv.innerHTML = '<span class="status-error">Disconnected</span>';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = type;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Start periodic updates
setInterval(updateSensorStatus, 500);