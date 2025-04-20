# Combining object detection with plant disease classification using a ResNet50 model and Flask

from flask import Flask, request, jsonify
import torch
import torchvision
from torchvision.transforms import functional as F
import numpy as np
import cv2
import tensorflow as tf

# Initialize Flask app
app = Flask(__name__)

# Load object detection model (Faster R-CNN pre-trained on COCO)
detection_model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=torchvision.models.detection.FasterRCNN_ResNet50_FPN_Weights.COCO_V1)
detection_model.eval()

# Load plant disease classification model (ResNet50-based)
plant_model = tf.keras.models.load_model("model")

# Class label mapping for disease classification
class_mapping = {
    "Apple_Scab_Leaf": "Apple___Apple_scab",
    "Apple_leaf": "Apple___healthy",
    "Apple_rust_leaf": "Apple___Cedar_apple_rust",
    "Blueberry_leaf": "Blueberry___healthy",
    "Cherry_leaf": "Cherry_(including_sour)___healthy",
    "Corn_Gray_leaf_spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_leaf_blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_rust_leaf": "Corn_(maize)___Common_rust_",
    "Peach_leaf": "Peach___healthy",
    "Potato_leaf_early_blight": "Potato___Early_blight",
    "Potato_leaf_late_blight": "Potato___Late_blight",
    "Raspberry_leaf": "Raspberry___healthy",
    "Soyabean_leaf": "Soybean___healthy",
    "Squash_Powdery_mildew_leaf": "Squash___Powdery_mildew",
    "Strawberry_leaf": "Strawberry___healthy",
    "Tomato_Early_blight_leaf": "Tomato___Early_blight",
    "Tomato_Septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "Tomato_leaf": "Tomato___healthy",
    "Tomato_leaf_bacterial_spot": "Tomato___Bacterial_spot",
    "Tomato_leaf_late_blight": "Tomato___Late_blight",
    "Tomato_leaf_mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "Tomato_leaf_yellow_virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato_mold_leaf": "Tomato___Leaf_Mold",
    "grape_leaf": "Grape___healthy",
    "grape_leaf_black_rot": "Grape___Black_rot"
}

# Make a reverse index for class predictions (assuming model outputs len(class_mapping) classes)
disease_labels = list(class_mapping.keys())

def run_inference(image):
    """Run object detection inference."""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_tensor = F.to_tensor(image_rgb)
    with torch.no_grad():
        predictions = detection_model([image_tensor])[0]
    return predictions

def classify_plant_disease(image):
    """Classify plant disease from cropped plant image."""
    image_resized = cv2.resize(image, (224, 224))
    image_resized = image_resized.astype('float32') / 255.0
    image_batch = np.expand_dims(image_resized, axis=0)
    prediction = plant_model.predict(image_batch)[0]
    class_id = np.argmax(prediction)
    confidence = float(prediction[class_id])
    disease_key = disease_labels[class_id]
    disease_name = class_mapping.get(disease_key, f"Unknown: {disease_key}")
    return {
        "class_id": int(class_id),
        "confidence": confidence,
        "disease_key": disease_key,
        "disease_name": disease_name
    }

COCO_LABELS = {
    64: "potted plant",  # Only care about 'potted plant' for this case
    1: "person", 17: "cat", 18: "dog", 19: "horse", 20: "sheep", 21: "cow",
    22: "elephant", 23: "bear", 24: "zebra", 25: "giraffe",
    62: "chair", 63: "couch"
}

@app.route('/predict', methods=['POST'])
def predict():
    try:
        file = request.files['image']
        img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
        detections = run_inference(img)
        h, w, _ = img.shape

        result = []

        for box, label, score in zip(detections['boxes'], detections['labels'], detections['scores']):
            class_id = label.item()
            score = score.item()
            if score > 0.5 and class_id in COCO_LABELS:
                x1, y1, x2, y2 = map(int, box.tolist())
                label_str = f"{COCO_LABELS[class_id]}: {score:.2f}"

                item = {
                    "object_label": label_str,
                    "bbox": [x1, y1, x2, y2],
                    "score": score
                }

                if COCO_LABELS[class_id] == "potted plant":
                    crop = img[y1:y2, x1:x2]
                    if crop.size > 0:
                        disease_result = classify_plant_disease(crop)
                        item["plant_disease_prediction"] = disease_result

                result.append(item)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

