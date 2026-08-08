# 🌱 Autonomous Crop Monitoring & Disease Detection Vehicle

An integrated **AI-powered autonomous field monitoring system** that combines computer vision, robotic vehicle control, sensor telemetry, and web-based monitoring into a single end-to-end platform.

The system is designed to demonstrate how **machine learning, embedded systems, computer vision, and real-time telemetry** can work together for intelligent field robotics and automated inspection.

---
## 📸 Media & Demonstration

### Hardware & System Setup

The following image shows the assembled crop-monitoring vehicle and its hardware/software setup.

<p align="center">
  <img src="WhatsApp Image 2026-08-05 at 22.00.39.jpeg" alt="Crop Disease Detection and Reporting Vehicle" width="800">
</p>

### 🎥 Live System Demonstration

The demonstration video shows the vehicle control interface, robotic movement, sensor telemetry, and AI-based plant monitoring pipeline.

<p align="center">
  <video src="WhatsApp Video 2026-08-05 at 22.00.38.mp4" controls width="800">
    Your browser does not support embedded videos.
  </video>
</p>

**[▶️ View / Download System Demonstration Video](WhatsApp Video 2026-08-05 at 22.00.38.mp4)**


> **Note:** GitHub's README renderer does not consistently support HTML5 video playback in all contexts. The direct video link above provides a reliable way to access the demonstration.



**Plant Disease Classification Notebook:**
[Kaggle — Plant Village Disease Classification Using Neural Networks](https://www.kaggle.com/code/carunmanikandan/plant-village-disease-classification-using-nn)

---

# 🧠 System Overview

The platform integrates four major subsystems:

```text
                  Autonomous Field Vehicle
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
     Camera System     Sensor System    Motor Control
          │                │                │
          ▼                ▼                ▼
    Plant Detection    IMU Telemetry    Arduino
          │                │                │
          ▼                ▼                ▼
   Disease Detection   Live Dashboard   Vehicle Control
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Flask Backend
                           │
                           ▼
                 Web Monitoring Interface
```

The resulting system provides a complete pipeline from **physical sensing → data acquisition → AI inference → decision support → visualization**.

---

# ✨ Key Capabilities

### 🤖 AI-Based Plant Detection

Uses **Faster R-CNN** to identify and localize plants from camera input before disease classification.

### 🌿 Plant Disease Classification

A neural-network-based image classification pipeline trained using the **PlantVillage dataset** is used to classify plant health conditions.

The model-development workflow is documented separately in the Kaggle notebook:

[Kaggle PlantVillage Disease Classification Notebook](https://www.kaggle.com/code/carunmanikandan/plant-village-disease-classification-using-nn)

The trained classification model can be integrated into the vehicle inference server for image-based disease identification.

### 📷 Two-Stage Computer Vision Pipeline

Instead of directly classifying an entire camera frame, the system follows a two-stage approach:

```text
Camera Frame
     ↓
Faster R-CNN
     ↓
Plant Detection / Localization
     ↓
Crop Plant Region
     ↓
Disease Classification Model
     ↓
Disease Prediction
```

This separates **object localization** from **disease classification**, making the computer-vision pipeline modular and easier to extend.

---

# 🚗 Robotic Vehicle Control

The vehicle uses an Arduino-based motor-control system for physical movement and actuator control.

Supported controls include:

* WASD keyboard controls
* Arrow-key controls
* Forward / backward movement
* Left / right steering
* Motor control
* Servo control

The architecture allows the web application to act as a high-level control interface while the Arduino handles low-level actuator control.

---

# 📡 Real-Time Telemetry

The vehicle collects motion telemetry through an IMU and exposes it through the web dashboard.

Tracked measurements include:

* 3-axis accelerometer data
* 3-axis gyroscope data
* Real-time sensor values
* Vehicle motion information
* Telemetry history

The dashboard uses **Chart.js** to visualize sensor measurements in real time.

```text
IMU Sensor
    ↓
I2C / Serial
    ↓
Flask Backend
    ↓
Telemetry API
    ↓
Chart.js Dashboard
```

The backend supports both:

* **I2C / SMBus telemetry**
* **Serial telemetry**

This allows the same software architecture to work with different hardware communication configurations.

---

# 🖥️ Web-Based Control & Monitoring

A Flask-based web application provides a unified interface for:

* Vehicle control
* Live telemetry
* AI inference status
* Sensor visualization
* Model-server communication
* Vehicle monitoring

The interface uses a responsive dark-themed dashboard with a glassmorphism-inspired design.

---

# 🧩 Software Architecture

```text
                        ┌──────────────────────┐
                        │     Web Dashboard    │
                        │      HTML / JS        │
                        └──────────┬───────────┘
                                   │
                              REST / HTTP
                                   │
                        ┌──────────▼───────────┐
                        │     Flask Backend    │
                        │       app.py         │
                        └──────┬─────┬─────────┘
                               │     │
                  ┌────────────┘     └──────────────┐
                  ▼                                 ▼
        ┌──────────────────┐             ┌──────────────────┐
        │ Telemetry Layer  │             │  Vehicle Control │
        │   I2C / Serial   │             │ Arduino / Motors │
        └────────┬─────────┘             └──────────────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ IMU Sensor Data  │
        └──────────────────┘

                              
                    AI INFERENCE PIPELINE
                               │
                               ▼
                     ┌─────────────────┐
                     │  server.py      │
                     │  ML Inference   │
                     └────────┬────────┘
                              │
                     ┌────────┴─────────┐
                     ▼                  ▼
              Faster R-CNN          ResNet50 /
              Plant Detection       Disease Classification
                     │                  │
                     └────────┬─────────┘
                              ▼
                     Disease Prediction
```

---

# 🌿 Machine Learning Pipeline

The disease-classification component is developed using the **PlantVillage dataset**.

### Training workflow

```text
PlantVillage Dataset
        ↓
Image Preprocessing
        ↓
Dataset Preparation
        ↓
Neural Network Training
        ↓
Validation / Evaluation
        ↓
Trained Classification Model
        ↓
Vehicle Inference Server
        ↓
Real-Time Prediction
```

The model-training experiments and dataset workflow are available in the Kaggle notebook:

[Kaggle PlantVillage Disease Classification Notebook](https://www.kaggle.com/code/carunmanikandan/plant-village-disease-classification-using-nn)

---

# 🔬 AI Inference Architecture

The deployed system separates **model development** from **model inference**.

### Model Development

```text
PlantVillage
     ↓
Training Notebook
     ↓
Neural Network
     ↓
Evaluation
     ↓
Saved Model
```

### Vehicle Deployment

```text
Vehicle Camera
     ↓
Inference Server
     ↓
Plant Detection
     ↓
Disease Classification
     ↓
Prediction
     ↓
Dashboard / Reporting
```

This separation allows the machine-learning model to be improved independently without redesigning the robotic control system.

---

# 🛡️ Fault-Tolerant Inference

The inference server includes a fallback simulation mode when the required TensorFlow/model assets are unavailable.

This allows the rest of the application stack to be tested independently of the ML model.

The architecture therefore separates:

* Vehicle control
* Telemetry
* Web interface
* Model inference

rather than coupling the complete system to a single ML component.

---

# 🗂️ Project Structure

```text
crop-disease-detection-vehicle/
│
├── app.py
│   └── Flask backend and monitoring dashboard API
│
├── server.py
│   └── Computer vision and ML inference server
│
├── mi.ino
│   └── Arduino motor and servo control
│
├── requirements.txt
│   └── Python dependencies
│
├── templates/
│   └── index.html
│       └── Web dashboard
│
└── README.md
```

---

# ⚙️ Technology Stack

### Artificial Intelligence

* TensorFlow
* Keras
* ResNet50
* Faster R-CNN
* PlantVillage Dataset

### Computer Vision

* OpenCV
* Image preprocessing
* Object detection
* Image classification

### Backend

* Python
* Flask
* REST APIs

### Embedded Systems

* Arduino
* IMU
* I2C / SMBus
* Serial communication
* DC motors
* Servo control

### Frontend

* HTML5
* CSS3
* JavaScript
* Chart.js

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone <repository-url>
cd crop-disease-detection-vehicle
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Python 3.8+ is recommended.

---

# 🔌 Hardware Setup

Upload the Arduino firmware:

```text
mi.ino
```

using the Arduino IDE.

The system requires the appropriate motor and servo libraries, including:

```text
AFMotor
Servo
```

Connect the IMU using the configured I2C interface or provide telemetry through the supported serial interface.

---

# ▶️ Running the System

### Start the AI inference server

```bash
python server.py
```

The inference service runs on:

```text
http://localhost:5001
```

### Start the vehicle dashboard

```bash
python app.py
```

The monitoring interface runs on:

```text
http://localhost:5000
```

Open the dashboard in a browser to control the vehicle and monitor telemetry.

---

# 📊 Engineering Highlights

This project demonstrates an end-to-end intelligent robotic system involving:

* **Computer vision**
* **Deep learning inference**
* **Object detection**
* **Image classification**
* **Real-time sensor telemetry**
* **Embedded motor control**
* **REST API development**
* **Web-based monitoring**
* **Hardware/software integration**
* **Fault-tolerant model serving**

The architecture is intentionally modular, allowing the sensing, AI, backend, and vehicle-control components to evolve independently.

---

# 🔮 Future Improvements

Potential extensions include:

* Autonomous navigation using visual perception
* GPS-based field mapping
* Multi-camera perception
* RGB + thermal image fusion
* Edge deployment using NVIDIA Jetson
* Real-time object tracking
* Crop health monitoring over time
* Remote vehicle operation
* Cloud-based telemetry storage
* Predictive crop-health analytics
* Automated field coverage planning

---

# 🎯 Project Relevance

This project demonstrates the engineering principles behind intelligent field systems:

**Sense → Analyze → Decide → Act → Monitor**

It combines physical sensing, machine learning, embedded control, and software infrastructure into a single deployable system.

The architecture can be extended beyond agricultural monitoring toward **industrial inspection, autonomous equipment, predictive maintenance, and intelligent connected machines**.

---

## 👨‍💻 Author

**Arunmanikandan C**

AI/ML Engineer · Computer Vision · Intelligent Systems · Full-Stack Development

[GitHub](https://github.com/) · [LinkedIn](https://www.linkedin.com/)
