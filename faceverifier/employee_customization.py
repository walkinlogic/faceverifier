import frappe
import cv2
import numpy as np
import mediapipe as mp
import os

mp_face_detection = mp.solutions.face_detection
# Load a pre-trained face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
def set_employee_image(doc, method):
    site_path = frappe.get_site_path()
    relative_path=""
    if doc.image:
        if doc.image.startswith('/private/files/'):
            relative_path = doc.image.replace('/private/files/', 'private/files/')
        elif doc.image.startswith('/files/'):
            relative_path = doc.image.replace('/files/', 'public/files/')

    if relative_path:
        image_path = os.path.join(site_path, relative_path)

        is_valid =  is_passport_photo(image_path)

        if is_valid[0]:
            return True
        else:
            return False
    
    return True


def is_passport_photo(image_path=''):
    logger = frappe.logger("passport_photo", allow_site=True) 
    logger.error(f"passport_photo endpoint hit. {str(image_path)}")
    img = cv2.imread(image_path)
    if img is None:
        return False, "Invalid image"

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Initialize Mediapipe Face Detection
    with mp_face_detection.FaceDetection(
        model_selection=1,  # Model 0: short-range (selfies), Model 1: full-range (passport-like photos)
        min_detection_confidence=0.8  # Only accept high-confidence faces
    ) as face_detection:

        results = face_detection.process(img_rgb)

        if not results.detections:
            logger.error("No face detected")
            return False, "No face detected"

        if len(results.detections) > 1:
            logger.error("Multiple faces detected")
            return False, "Multiple faces detected"

        # Only one face detected
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        img_h, img_w, _ = img.shape

        # Face bounding box dimensions
        face_width = bbox.width * img_w
        face_height = bbox.height * img_h
        face_area = face_width * face_height
        img_area = img_w * img_h
        face_percentage = (face_area / img_area) * 100

        # if not (30 <= face_percentage <= 70):
        #     return False, "Face size not appropriate (should occupy 30-70% of the image)"

        # Check if face is roughly centered
        face_center_x = bbox.xmin + bbox.width / 2
        if not (0.4 <= face_center_x <= 0.6):
            logger.error("Face not centered horizontally")
            return False, "Face not centered horizontally"
    logger.error("Looks like a valid passport photo!")
    return True, "Looks like a valid passport photo!"