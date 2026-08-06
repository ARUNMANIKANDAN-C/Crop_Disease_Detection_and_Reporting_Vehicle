from flask import Flask, jsonify, render_template, request, Response
import cv2
import time
import json
import threading
import serial
import serial.tools.list_ports
import os
import requests

# Try to import smbus for Raspberry Pi I2C connection
try:
    import smbus
    HAS_SMBUS = True
except ImportError:
    HAS_SMBUS = False

app = Flask(__name__)

# Server URL for inference (model server)
MODEL_SERVER_URL = 'http://localhost:5001/predict'

# Shared IMU telemetry data
imu_data = {
    "Ax": 0.0, "Ay": 0.0, "Az": 0.0,
    "Gx": 0.0, "Gy": 0.0, "Gz": 0.0
}

# Serial settings
ser = None
selected_serial_port = None

# Camera settings
camera_capture = None
camera_index = None

# Scan thread control (for telemetry reading)
scan_thread = None
scan_active = False

# Path to save images
SAVE_PATH = "detected_images"
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

# MPU6050 Registers and Address (I2C)
MPU_ADDR = 0x68
PWR_MGMT_1 = 0x6B 
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H = 0x43

# -------------------- Telemetry Loop --------------------
def read_raw_i2c_data(bus, addr):
    try:
        high = bus.read_byte_data(MPU_ADDR, addr)
        low = bus.read_byte_data(MPU_ADDR, addr + 1)
        value = (high << 8) | low
        if value > 32768:
            value -= 65536
        return value
    except Exception:
        return 0

def telemetry_loop():
    global scan_active, imu_data, ser
    
    # Try setting up SMBus (I2C)
    bus = None
    if HAS_SMBUS:
        try:
            bus = smbus.SMBus(1)
            bus.write_byte_data(MPU_ADDR, PWR_MGMT_1, 0)
            print("[IMU] Successfully initialized MPU6050 via I2C.")
        except Exception as e:
            print(f"[IMU] Failed to initialize MPU6050 via I2C: {e}")
            bus = None

    while scan_active:
        # Option A: Read from I2C directly
        if bus is not None:
            try:
                acc_x = read_raw_i2c_data(bus, ACCEL_XOUT_H)
                acc_y = read_raw_i2c_data(bus, ACCEL_XOUT_H + 2)
                acc_z = read_raw_i2c_data(bus, ACCEL_XOUT_H + 4)
                gyro_x = read_raw_i2c_data(bus, GYRO_XOUT_H)
                gyro_y = read_raw_i2c_data(bus, GYRO_XOUT_H + 2)
                gyro_z = read_raw_i2c_data(bus, GYRO_XOUT_H + 4)

                imu_data = {
                    "Ax": round(acc_x / 16384.0, 2),
                    "Ay": round(acc_y / 16384.0, 2),
                    "Az": round(acc_z / 16384.0, 2),
                    "Gx": round(gyro_x / 131.0, 2),
                    "Gy": round(gyro_y / 131.0, 2),
                    "Gz": round(gyro_z / 131.0, 2),
                }
            except Exception as e:
                print(f"[IMU] I2C read error: {e}")
        
        # Option B: Read from Serial (if serial is connected and JSON is expected)
        elif ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith('{') and line.endswith('}'):
                        data = json.loads(line)
                        imu_data.update(data)
            except Exception:
                pass
        
        # Option C: Simulation / Idle (mock random walking to ensure UI gets data)
        else:
            import random
            imu_data = {
                "Ax": round(random.uniform(-0.1, 0.1), 2),
                "Ay": round(random.uniform(-0.1, 0.1), 2),
                "Az": round(1.0 + random.uniform(-0.05, 0.05), 2),
                "Gx": round(random.uniform(-1, 1), 2),
                "Gy": round(random.uniform(-1, 1), 2),
                "Gz": round(random.uniform(-1, 1), 2),
            }

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
        print(f"[Serial] Opened serial port: {port}")
        return True
    except Exception as e:
        print(f"[Serial] Failed to open serial port {port}: {e}")
        return False

# -------------------- Camera Functions --------------------
def list_camera_indices(max_test=5):
    available = []
    for i in range(max_test):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            success, _ = cap.read()
            if success:
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
            if not success:
                time.sleep(0.03)
                continue
            
            # Encode frame to JPEG bytes to send to inference server
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_bytes = img_encoded.tobytes()

            detections = []
            try:
                # Post frame to prediction server
                response = requests.post(MODEL_SERVER_URL, files={'image': img_bytes}, timeout=0.5)
                if response.status_code == 200:
                    detections = response.json()
            except Exception as e:
                # Silently bypass if inference server is down or times out
                pass

            # Draw bounding boxes and details on the stream frame
            for detection in detections:
                bbox = detection.get('bbox')
                if not bbox or len(bbox) != 4:
                    continue
                
                x1, y1, x2, y2 = bbox
                label = detection.get('object_label', 'Object')
                
                # Check for nested plant disease prediction
                if 'plant_disease_prediction' in detection:
                    dis = detection['plant_disease_prediction']
                    label = f"{dis['disease_name']} ({dis['confidence']:.2f})"
                    
                    # Highlight disease detection in red
                    box_color = (0, 0, 255) if "healthy" not in dis['disease_name'].lower() else (0, 255, 0)
                    
                    # Save image of detected disease
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    file_path = os.path.join(SAVE_PATH, f"disease_{timestamp}.jpg")
                    cv2.imwrite(file_path, frame)
                else:
                    box_color = (0, 255, 0)

                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.5)

# -------------------- Flask Routes --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connections')
def get_connections():
    ports = list_serial_ports()
    cameras = list_camera_indices()
    return jsonify({
        "ports": ports,
        "cameras": cameras
    })

@app.route('/command', methods=['POST'])
def handle_command():
    global ser
    data = request.get_json()
    cmd = data.get('cmd', '')
    
    # Normalize command mappings:
    # S1:value or S2:value -> SERVO:value
    if cmd.startswith("S1:") or cmd.startswith("S2:"):
        _, value = cmd.split(":")
        cmd = f"SERVO:{value}"
    
    print(f"[Command] Dispatching serial command: {cmd}")
    
    if ser and ser.is_open:
        try:
            ser.write((cmd + "\n").encode())
            return jsonify({"status": "sent", "cmd": cmd})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Write failed: {e}"})
    
    return jsonify({"status": "warning", "message": "Command printed (Serial not connected)", "cmd": cmd})

@app.route('/imu')
def get_imu():
    return jsonify(imu_data)

@app.route('/set_serial', methods=['POST'])
def set_serial():
    global selected_serial_port
    data = request.get_json()
    selected_serial_port = data.get('port')
    success = open_serial(selected_serial_port)
    return jsonify({"status": "Connected" if success else "Failed", "port": selected_serial_port})

@app.route('/set_camera', methods=['POST'])
def set_camera():
    global camera_index
    data = request.get_json()
    index = data.get('index', 0)
    success = open_camera(index)
    if success:
        camera_index = index
        return jsonify({"status": "Connected", "index": index})
    return jsonify({"status": "Failed", "index": index})

@app.route('/video_feed')
def video_feed():
    if camera_capture and camera_capture.isOpened():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Camera not connected", 400

@app.route('/scan/start')
def start_scan():
    global scan_active, scan_thread
    if not scan_active:
        scan_active = True
        scan_thread = threading.Thread(target=telemetry_loop, daemon=True)
        scan_thread.start()
        return jsonify({"status": "Telemetry tracking started"})
    return jsonify({"status": "Telemetry tracking already active"})

@app.route('/scan/stop')
def stop_scan():
    global scan_active
    if scan_active:
        scan_active = False
        return jsonify({"status": "Telemetry tracking stopped"})
    return jsonify({"status": "Telemetry tracking is not active"})

if __name__ == '__main__':
    # Auto-detect first serial port on startup if possible
    ports = list_serial_ports()
    if ports:
        selected_serial_port = ports[0]
        open_serial(selected_serial_port)
    else:
        print("[Startup] No active serial ports detected.")

    app.run(host='0.0.0.0', port=5000, debug=True)
