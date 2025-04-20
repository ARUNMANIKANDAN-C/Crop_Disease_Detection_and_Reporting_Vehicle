from flask import Flask, jsonify, render_template_string, request, Response
import cv2, time, json, threading
import serial, serial.tools.list_ports
from multiprocessing import Manager
import smbus
import os

app = Flask(__name__)

# Server URL for inference (model server)
MODEL_SERVER_URL = 'http://192.168.9.177:5001/predict'

# Shared IMU data
manager = Manager()
imu_data = manager.dict()

# Serial settings
ser = None
selected_serial_port = '/dev/ttyUSB0'

# Camera
camera_capture = None
camera_index = None

# Scan thread control
scan_thread = None
scan_active = False

# Path to save images
SAVE_PATH = "detected_images"
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

# -------------------- IMU Reader --------------------
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B 
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43
bus = smbus.SMBus(1)

def read_raw_data(addr):
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr + 1)
    value = (high << 8) | low
    if value > 32768:
        value -= 65536
    return value

def imu_loop(shared_dict):
    bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)
    while True:
        try:
            acc_x = read_raw_data(ACCEL_XOUT_H)
            acc_y = read_raw_data(ACCEL_XOUT_H + 2)
            acc_z = read_raw_data(ACCEL_XOUT_H + 4)
            gyro_x = read_raw_data(GYRO_XOUT_H)
            gyro_y = read_raw_data(GYRO_XOUT_H + 2)
            gyro_z = read_raw_data(GYRO_XOUT_H + 4)

            shared_dict.update({
                "Ax": round(acc_x / 16384.0, 2),
                "Ay": round(acc_y / 16384.0, 2),
                "Az": round(acc_z / 16384.0, 2),
                "Gx": round(gyro_x / 131.0, 2),
                "Gy": round(gyro_y / 131.0, 2),
                "Gz": round(gyro_z / 131.0, 2),
            })
        except:
            continue
        time.sleep(0.1)

# -------------------- Serial Functions --------------------
def list_serial_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def open_serial(port):
    global ser
    try:
        if ser and ser.is_open:
            ser.close()
        ser = serial.Serial(port, 9600, timeout=1)
        return True
    except Exception as e:
        print(f"Failed to open serial port {port}: {e}")
        return False

# -------------------- Camera Functions --------------------
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
                _, img_encoded = cv2.imencode('.jpg', frame)
                img_bytes = img_encoded.tobytes()
                response = requests.post(MODEL_SERVER_URL, files={'image': img_bytes})

                if response.status_code == 200:
                    detections = response.json()
                    for detection in detections:
                        x1, y1, x2, y2 = detection['bbox']
                        label = detection['label']

                        # Save image if 'potted plant' is detected
                        if label == "potted plant":
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            file_path = os.path.join(SAVE_PATH, f"potted_plant_{timestamp}.jpg")
                            cv2.imwrite(file_path, frame)

                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                                    0.6, (0, 255, 0), 2)

                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(1)

# -------------------- Flask Routes --------------------
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
            body {{ font-family: Arial; background-color: #f4f4f4; padding: 20px; }}
            h1, h3 {{ color: #333; }}
            select, button, input[type=range] {{
                margin: 5px; padding: 8px; font-size: 1rem;
                border-radius: 5px; border: 1px solid #ccc;
            }}
            button {{ background-color: #007BFF; color: white; cursor: pointer; }}
            button:hover {{ background-color: #0056b3; }}
            pre {{ background: #fff; padding: 10px; border-radius: 8px; }}
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

            function startScan() {{
                fetch('/scan/start').then(res => res.json()).then(alert);
            }}

            function stopScan() {{
                fetch('/scan/stop').then(res => res.json()).then(alert);
            }}

            setInterval(updateIMU, 200);
        </script>
    </head>
    <body>
        <h1>IMU + Camera Control Panel</h1>
        <h3>Serial Port</h3>
        <select id="portSelect">{''.join(f'<option value="{p}">{p}</option>' for p in ports)}</select>
        <button onclick="setSerialPort()">Connect Serial</button>

        <h3>Camera</h3>
        <select id="camSelect">{''.join(f'<option value="{i}">Camera {i}</option>' for i in cams)}</select>
        <button onclick="setCamera()">Connect Camera</button>

        <h3>Camera Stream</h3>
        <img id="cameraFeed" width="480" height="360" style="display:none"/>

        <h3>IMU Data</h3>
        <pre id="imu">Loading...</pre>

        <h3>Motor Control</h3>
        <button onclick="sendCommand('FORWARD')">Forward</button>
        <button onclick="sendCommand('BACKWARD')">Backward</button>
        <button onclick="sendCommand('LEFT')">Left</button>
        <button onclick="sendCommand('RIGHT')">Right</button>
        <button onclick="sendCommand('STOP')">Stop</button>

        <h3>Scan Control</h3>
        <button onclick="startScan()">Start Scan</button>
        <button onclick="stopScan()">Stop Scan</button>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/command', methods=['POST'])
def command():
    data = request.get_json()
    cmd = data['cmd']
    print(f"Received command: {cmd}")
    return jsonify({"status": "Command received", "cmd": cmd})

@app.route('/imu')
def get_imu():
    return jsonify(imu_data)

@app.route('/set_serial', methods=['POST'])
def set_serial():
    data = request.get_json()
    global selected_serial_port
    selected_serial_port = data['port']
    success = open_serial(selected_serial_port)
    return jsonify({"status": "Connected" if success else "Failed", "port": selected_serial_port})

@app.route('/set_camera', methods=['POST'])
def set_camera():
    global camera_index
    data = request.get_json()
    camera_index = data['index']
    success = open_camera(camera_index)
    return jsonify({"status": "Connected" if success else "Failed", "index": camera_index})

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/scan/start')
def start_scan():
    global scan_active, scan_thread
    if not scan_active:
        scan_thread = threading.Thread(target=imu_loop, args=(imu_data,))
        scan_thread.start()
        scan_active = True
        return jsonify({"status": "Scan started"})
    return jsonify({"status": "Scan already active"})

@app.route('/scan/stop')
def stop_scan():
    global scan_active, scan_thread
    if scan_active:
        scan_active = False
        scan_thread.join()
        return jsonify({"status": "Scan stopped"})
    return jsonify({"status": "No active scan"})

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
