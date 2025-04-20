from flask import Flask, jsonify, render_template_string, request, Response
import serial, threading, time, json, cv2
import serial.tools.list_ports

app = Flask(__name__)

# Serial related
ser = None
imu_data = {}
selected_serial_port = None  # Auto-detected later

# Camera related
camera_capture = None
camera_index = None  # Don't open by default

# ---------- Serial Functions ----------
def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def open_serial(port):
    global ser
    try:
        if ser and ser.is_open:
            ser.close()
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Opened serial port: {port}")
        return True
    except Exception as e:
        print(f"Failed to open serial port {port}: {e}")
        return False

def read_serial():
    global imu_data
    while True:
        if ser and ser.is_open:
            try:
                line = ser.readline().decode('utf-8').strip()
                imu_data = json.loads(line)
            except:
                continue
        else:
            time.sleep(1)

# Start serial reading thread
threading.Thread(target=read_serial, daemon=True).start()

# ---------- Camera Functions ----------
def list_camera_indices(max_test=5):
    available = []
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            available.append(i)
        cap.release()
    return available

def open_camera(index):
    global camera_capture
    if camera_capture:
        camera_capture.release()
    camera_capture = cv2.VideoCapture(index)
    return camera_capture.isOpened()

def generate_frames():
    while True:
        if camera_capture and camera_capture.isOpened():
            success, frame = camera_capture.read()
            if success:
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(1)

# ---------- Flask Routes ----------
@app.route('/')
def index():
    ports = list_serial_ports()
    cams = list_camera_indices()
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IMU & Camera Dashboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            h3 {{
                color: #555;
            }}
            select, button, input[type=range] {{
                padding: 8px;
                margin: 5px;
                font-size: 1rem;
                border-radius: 5px;
                border: 1px solid #ccc;
            }}
            button {{
                background-color: #007BFF;
                color: white;
                border: none;
                cursor: pointer;
            }}
            button:hover {{
                background-color: #0056b3;
            }}
            #imu {{
                background-color: #fff;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 8px;
                white-space: pre-wrap;
                font-size: 1rem;
                max-height: 200px;
                overflow-y: auto;
            }}
            img {{
                border: 2px solid #444;
                border-radius: 10px;
                display: block;
                margin-bottom: 20px;
            }}
        </style>
        <script>
            function sendCommand(cmd) {{
                fetch('/command', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ cmd }})
                }});
            }}

            function updateIMU() {{
                fetch('/imu')
                    .then(res => res.json())
                    .then(data => {{
                        document.getElementById('imu').innerText = JSON.stringify(data, null, 2);
                    }});
            }}

            function setSerialPort() {{
                const port = document.getElementById('portSelect').value;
                fetch('/set_serial', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ port }})
                }}).then(res => res.json()).then(data => {{
                    alert(data.status + ": " + data.port);
                }});
            }}

            function setCamera() {{
                const index = document.getElementById('camSelect').value;
                fetch('/set_camera', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ index: parseInt(index) }})
                }}).then(res => res.json()).then(data => {{
                    alert(data.status + " - Camera index: " + data.index);
                    if (data.status === "Connected") {{
                        const cam = document.getElementById('cameraFeed');
                        cam.src = '/video_feed';
                        cam.style.display = 'block';
                    }}
                }});
            }}

            setInterval(updateIMU, 200);
        </script>
    </head>
    <body>
        <h1>IMU + Camera Control Panel</h1>

        <h3>Serial Port Selection</h3>
        <select id="portSelect">
            {''.join(f'<option value="{p}">{p}</option>' for p in ports)}
        </select>
        <button onclick="setSerialPort()">Connect Serial</button>

        <h3>Camera Selection</h3>
        <select id="camSelect">
            {''.join(f'<option value="{i}">Camera {i}</option>' for i in cams)}
        </select>
        <button onclick="setCamera()">Connect Camera</button>

        <h3>Live Camera Stream</h3>
        <img id="cameraFeed" width="480" height="360" style="display:none"/>

        <h3>IMU Data</h3>
        <pre id="imu">Loading...</pre>

        <h3>Motor Control</h3>
        <button onclick="sendCommand('FORWARD')">Forward</button>
        <button onclick="sendCommand('BACKWARD')">Backward</button>
        <button onclick="sendCommand('LEFT')">Left</button>
        <button onclick="sendCommand('RIGHT')">Right</button>
        <button onclick="sendCommand('STOP')">Stop</button>

        <h3>Servo Control</h3>
        Servo 1: <input type="range" min="0" max="180" onchange="sendCommand('S1:' + this.value)"><br>
        Servo 2: <input type="range" min="0" max="180" onchange="sendCommand('S2:' + this.value)">
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/imu')
def get_imu():
    return jsonify(imu_data)

@app.route('/command', methods=['POST'])
def send_command():
    cmd = request.json.get('cmd')
    if ser and ser.is_open:
        ser.write((cmd + "\n").encode())
        return jsonify({"status": "sent", "cmd": cmd})
    return jsonify({"status": "error", "message": "Serial port not connected."})

@app.route('/set_serial', methods=['POST'])
def set_serial():
    global selected_serial_port
    selected_serial_port = request.json.get('port')
    success = open_serial(selected_serial_port)
    return jsonify({"status": "Connected" if success else "Failed", "port": selected_serial_port})

@app.route('/set_camera', methods=['POST'])
def set_camera():
    global camera_index
    index = request.json.get('index')
    success = open_camera(index)
    if success:
        camera_index = index
        return jsonify({"status": "Connected", "index": index})
    else:
        return jsonify({"status": "Failed", "index": index})

@app.route('/video_feed')
def video_feed():
    if camera_capture and camera_capture.isOpened():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not connected", 400

if __name__ == '__main__':
    ports = list_serial_ports()
    if ports:
        selected_serial_port = ports[0]  # Auto-select first available
        open_serial(selected_serial_port)
    else:
        print("No serial ports found.")
    app.run(host='0.0.0.0', port=5000, debug=True)
