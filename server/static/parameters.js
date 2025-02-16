// Parameters page functionality
let updateTimeout;

function updateParam(name, value) {
    // Update displayed value
    event.target.nextElementSibling.textContent = Number(value).toFixed(3);
    
    // Debounce the API call
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`/param_update?name=${name}&value=${value}`);
            const data = await response.json();
            showStatus(data.success ? 'success' : 'error', data.message);
        } catch (error) {
            showStatus('error', 'Failed to update parameter');
            console.error('Error:', error);
        }
    }, 100);
}

function showStatus(type, message) {
    const notification = document.getElementById('notification');
    notification.className = type;
    notification.textContent = message;
    notification.style.display = 'block';
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 2000);
}

// Update monitoring data
async function updateMonitoringData() {
    try {
        const response = await fetch('/monitor_data');
        const data = await response.json();
        
        // Update Kalman filter displays
        document.getElementById('kalman_x').textContent = 
            `X: ${data.kalman_x.value.toFixed(3)} (Q: ${data.kalman_x.Q.toFixed(3)})`;
        document.getElementById('kalman_y').textContent = 
            `Y: ${data.kalman_y.value.toFixed(3)} (Q: ${data.kalman_y.Q.toFixed(3)})`;
        
        // Update PID status
        document.getElementById('pid_status').textContent = 
            `Error: ${data.pid_error.toFixed(3)}`;
        
        // Update stability metric
        document.getElementById('stability').textContent = 
            data.stability.toFixed(1);
            
        // Update slider positions if they've changed server-side
        updateSliderPositions(data.parameters);
        
    } catch (error) {
        console.error('Error updating monitoring data:', error);
    }
}

function updateSliderPositions(parameters) {
    // Update each slider if its value has changed server-side
    for (const [name, value] of Object.entries(parameters)) {
        const slider = document.querySelector(`input[oninput*="updateParam('${name}'"]`);
        if (slider && Math.abs(slider.value - value) > 0.001) {
            slider.value = value;
            slider.nextElementSibling.textContent = value.toFixed(3);
        }
    }
}

// Start periodic updates
setInterval(updateMonitoringData, 500);