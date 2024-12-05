import os
import json
import pyautogui
import cv2
import numpy as np
from PIL import Image
import pytesseract
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QFileDialog
import sys

# Load configuration file
def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    else:
        print("Configuration file not found!")
        return {}

# Take a screenshot
def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot_path = os.path.join(os.getcwd(), "screenshot.png")
    screenshot.save(screenshot_path)
    return screenshot_path

# Perform OCR
def perform_ocr(screenshot_path, config):
    image = Image.open(screenshot_path)
    team1_coords = config["team1_coords"]
    x_start = int(team1_coords[0] * image.width)
    y_start = int(team1_coords[1] * image.height)
    x_end = x_start + int(team1_coords[2] * image.width)
    y_end = y_start + int(team1_coords[3] * image.height)

    cropped_image = image.crop((x_start, y_start, x_end, y_end))
    cropped_image = preprocess_image(cropped_image)

    text = pytesseract.image_to_string(cropped_image, config="--psm 6")
    print("Extracted text:", text)

# Preprocess image for better OCR
def preprocess_image(image):
    resized_image = image.resize((500, int(500 * (image.height / image.width))), Image.ANTIALIAS)
    return resized_image.convert("L")  # Convert to grayscale

# GUI Application
def start_gui():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Game Data Extractor")

    layout = QVBoxLayout()

    label = QLabel("Welcome to the Game Data Extractor!")
    layout.addWidget(label)

    start_button = QPushButton("Take Screenshot and Extract Data")
    start_button.clicked.connect(lambda: perform_ocr(take_screenshot(), config))
    layout.addWidget(start_button)

    exit_button = QPushButton("Exit")
    exit_button.clicked.connect(app.quit)
    layout.addWidget(exit_button)

    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())

# Load configuration and start GUI
if __name__ == "__main__":
    config = load_config()
    start_gui()
