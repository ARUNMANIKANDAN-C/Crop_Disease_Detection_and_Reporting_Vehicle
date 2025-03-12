from flask import Flask, render_template_string, Response, request, jsonify
import cv2
import serial
import time

app = Flask(__name__)

# === Arduino Serial Setup ===
try:
    arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
    time.sleep(2)
except Exception as e:
    print(f"[ERROR] Arduino not found: {e}")
    arduino = None

def send_command(cmd):
    if arduino:
        try:
            arduino.write((cmd + '\n').encode())
            time.sleep(0.05)
            return arduino.readline().decode().strip()
        except:
            return "Error writing to Arduino"
    return "Arduino not connected"

# === Camera Setup ===
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# === Flask Routes ===
@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/command', methods=['POST'])
def command():
    data = request.json
    cmd_type = data.get('type')
    
    if cmd_type == 'move':
        cmd = data.get('cmd', 'S')  # Send e.g., "F:150"
    elif cmd_type == 'servo':
        angle = int(data.get('angle', 90))
        cmd = f"SERVO:{angle}"      # Fixed: correct format
    else:
        cmd = "S"

    result = send_command(cmd)
    return jsonify(status=result)

@app.route('/status')
def status():
    return jsonify(connected=bool(arduino))

# === HTML Page ===
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Rocky Bridge Control</title>
  <style>
    body { font-family: Arial; text-align: center; background: #f9f9f9; }
    h2 { margin-top: 20px; }
    button {
      padding: 12px 24px;
      margin: 8px;
      font-size: 18px;
      background-color: #4285f4;
      color: white;
      border: none;
      border-radius: 6px;
      cursor: pointer;
    }
    button:hover { background-color: #3367d6; }
    #camera {
      margin-top: 30px;
      width: 400px;
      border: 4px solid #444;
      border-radius: 10px;
    }
    #status-bar {
      background: #222;
      color: white;
      padding: 10px;
      font-size: 18px;
    }
    #servo-container {
      margin-top: 30px;
    }
    input[type=range] {
      width: 300px;
    }
  </style>
</head>
<body>

  <div id="status-bar">
    Arduino Status: <span id="arduino-status">Checking...</span>
  </div>

  <h2>Rocky Bridge Movement Control</h2>
  <div>
    <button onclick="sendCmd('F:150')">Forward</button><br>
    <button onclick="sendCmd('L:150')">Left</button>
    <button onclick="sendCmd('S')">Stop</button>
    <button onclick="sendCmd('R:150')">Right</button><br>
    <button onclick="sendCmd('B:150')">Backward</button>
  </div>

  <div id="servo-container">
    <h3>Servo Angle</h3>
    <input type="range" min="0" max="180" value="90" id="servoSlider" oninput="updateServo(this.value)">
    <p>Angle: <span id="servoValue">90</span>°</p>
    <button onclick="sendCmd('SWEEP')">Sweep Servo</button>
  </div>

  <h3>Live Camera Feed</h3>
  <img src="/video_feed" id="camera">

  <script>
    function sendCmd(cmd) {
      fetch('/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'move', cmd })
      });
    }

    function updateServo(val) {
      document.getElementById('servoValue').innerText = val;
      fetch('/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'servo', angle: parseInt(val) })
      });
    }

    function updateStatus() {
      fetch('/status').then(res => res.json()).then(data => {
        const el = document.getElementById('arduino-status');
        if (data.connected) {
          el.innerText = "Connected ✅";
          el.style.color = "lightgreen";
        } else {
          el.innerText = "Disconnected ❌";
          el.style.color = "red";
        }
      });
    }

    updateStatus();
    setInterval(updateStatus, 3000);
  </script>
</body>
</html>
"""

# === Run the Flask App ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
