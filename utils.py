import os
import json
import uuid
import shutil
import pandas as pd
from PIL import Image
import pytesseract
import cv2
import numpy as np
import csv
from datetime import datetime
import sys


# Determine the base path depending on whether the code is "frozen" by PyInstaller or not
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

# Set the Tesseract executable path relative to base_path
pytesseract.pytesseract.tesseract_cmd = os.path.join(base_path, "tesseract", "tesseract.exe")

def generate_uuid():
    return str(uuid.uuid4())

def load_config(config_file="config.json"):
    with open(config_file, "r") as f:
        return json.load(f)

def clear_session_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)
    print(f"Cleared and prepared session folder: {folder_path}")

def crop_area(image, start_x, end_x, top_y, bottom_y):
    width, height = image.size
    return image.crop((
        int(start_x / 100 * width),
        int(top_y / 100 * height),
        int(end_x / 100 * width),
        int(bottom_y / 100 * height)
    ))

def detect_top_left_corner(screenshot, template_path="team1_template.png", threshold=0.8):
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template file not found: {template_path}")

    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        raise ValueError("Top-left corner not detected. Check the template or screenshot.")

    return max_loc  # (x, y) of the detected top-left corner

def extract_text_from_image(cropped_image, is_numeric=False):
    gray_image = cropped_image.convert("L")  # grayscale
    config = "--psm 6"
    if is_numeric:
        config += " outputbase digits"
    return pytesseract.image_to_string(gray_image, config=config).strip()

def save_cropped_image(image, output_folder, file_name):
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(output_folder, file_name)
    image.save(file_path)
    print(f"Saved cropped image: {file_path}")

def process_middle_control(image, middle_control, output_folder, uuid_str):
    middle_control_data = []
    for team, coords in middle_control.items():
        cropped_team_area = crop_area(
            image,
            coords["top_left_x"],
            coords["bottom_right_x"],
            coords["top_left_y"],
            coords["bottom_right_y"]
        )
        save_cropped_image(cropped_team_area, output_folder, f"Middle_Control_{team.replace(' ', '_')}.png")
        extracted_time = extract_text_from_image(cropped_team_area).strip()
        if ":" not in extracted_time:
            extracted_time = "00:00"
        try:
            minutes, seconds = map(int, extracted_time.split(":"))
            middle_control_seconds = minutes * 60 + seconds
        except ValueError:
            extracted_time = "00:00"
            middle_control_seconds = 0
        middle_control_data.append([uuid_str, team, extracted_time, middle_control_seconds])
        print(f"Middle Control for {team}: {extracted_time} ({middle_control_seconds} seconds)")
    return middle_control_data

def append_to_aggregate(data_file, new_data_file):
    # Read existing aggregate data if available
    try:
        aggregate_data = pd.read_csv(data_file)
    except FileNotFoundError:
        aggregate_data = pd.DataFrame()

    # Read new data
    new_data = pd.read_csv(new_data_file)

    # Append new data to the aggregate
    aggregate_data = pd.concat([aggregate_data, new_data], ignore_index=True)

    # Save back to the aggregate file
    aggregate_data.to_csv(data_file, index=False)
    print(f"Data aggregated into {data_file}")

def save_middle_control_to_csv(data, output_file):
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["uuid", "team", "timeMMSS", "middleControlSeconds"])
        writer.writerows(data)
    print(f"Middle control data saved to {output_file}")

def save_to_csv(data, output_file, uuid_str):
    # Data is expected as a list of lists: [row_name, player_name, level, score, kills, damage, goldSpent, team, game_outcome, datetime]
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["uuid", "row", "player", "level", "score", "kills", "damage", "goldSpent", "team", "Victory/Defeat", "datetime"])
        for row in data:
            writer.writerow([uuid_str] + row)
    print(f"Data saved to {output_file}")

def detect_victory_or_defeat(image, victory_position):
    cropped_victory_area = image.crop((
        int(victory_position["start_x"]),
        int(victory_position["start_y"]),
        int(victory_position["end_x"]),
        int(victory_position["end_y"])
    ))

    # Use LAST_SESSION_FOLDER instead of "session_data"
    # Import LAST_SESSION_FOLDER at the top of utils.py or pass it as a parameter
    # For simplicity, just hardcode it if needed:
    LAST_SESSION_FOLDER = os.path.join("data", "last_session")
    os.makedirs(LAST_SESSION_FOLDER, exist_ok=True)

    victory_defeat_path = os.path.join(LAST_SESSION_FOLDER, "victory_defeat_area.png")
    cropped_victory_area.save(victory_defeat_path)

    result_text = extract_text_from_image(cropped_victory_area).strip().lower()
    if "victory" in result_text:
        return "Victory"
    elif "defeat" in result_text:
        return "Defeat"
    return "Unknown"
