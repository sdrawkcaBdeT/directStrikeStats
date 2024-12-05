import os
import json
import csv
import uuid
import shutil
import pandas as pd
from datetime import datetime
from PIL import Image
import pytesseract
import pyautogui
import cv2
import numpy as np

from utils import (
    generate_uuid, clear_session_folder, load_config, detect_victory_or_defeat,
    process_middle_control, save_to_csv, save_middle_control_to_csv, append_to_aggregate,
    extract_text_from_image, save_cropped_image, crop_area
)

DATA_FOLDER = "data/"
LAST_SESSION_FOLDER = os.path.join(DATA_FOLDER, "last_session")

# Make sure data folders exist
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), "tesseract", "tesseract.exe")

def process_screenshot(player_name):
    # Generate UUID for the session
    session_uuid = generate_uuid()

    # Prepare session directory
    clear_session_folder(LAST_SESSION_FOLDER)

    # Load the config
    config = load_config()

    # Take a full screenshot
    screenshot_path = os.path.join(LAST_SESSION_FOLDER, "screenshot.png")
    pyautogui.screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    # Open the screenshot image
    image = Image.open(screenshot_path)

    # Convert the screenshot to OpenCV format
    screenshot_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Load the team1 template for top-left corner detection
    template_path = "team1_template.png"
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print(f"Template file not found: {template_path}")
        return

    # Perform template matching
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Threshold to ensure a match was found
    threshold = 0.8  # Adjust as needed
    if max_val < threshold:
        print("Top-left corner not detected. Ensure the template matches the screenshot.")
        return

    # Top-left corner of the matched region
    top_left = max_loc
    print(f"Top-left corner detected at: {top_left}")

    # Crop the region starting from the detected top-left corner
    # These ratios were used previously and found to work correctly.
    # Adjust if necessary for your resolution.
    cropped_image = screenshot_cv[
        top_left[1]:top_left[1] + int(915 / 1440 * screenshot_cv.shape[0]),  # Height
        top_left[0]:top_left[0] + int(1665 / 2560 * screenshot_cv.shape[1])  # Width
    ]

    # Convert cropped image back to PIL format for further processing
    cropped_image_pil = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))

    # Save the cropped scoreboard image for debugging
    save_cropped_image(cropped_image_pil, LAST_SESSION_FOLDER, "scoreboard_cropped.png")

    # Detect Victory/Defeat
    victory_defeat_position = config["victory_defeat_position"]
    game_outcome = detect_victory_or_defeat(cropped_image_pil, victory_defeat_position)

    rows = config["rows"]
    columns = config["columns"]
    extracted_data = []

    # Process each player row and extract stats
    for i, row in enumerate(rows):
        print(f"Processing Row {i + 1}")
        row_data = [f"Row {i + 1}"]

        # Determine the player's team
        team = "Team 1" if i < 3 else "Team 2"

        for column_name, column_coords in columns.items():
            cropped_cell = crop_area(
                cropped_image_pil,
                column_coords["start_x"],
                column_coords["end_x"],
                row["top_y"],
                row["bottom_y"]
            )
            save_cropped_image(
                cropped_cell,
                LAST_SESSION_FOLDER,
                f"Row_{i+1}_{column_name.replace(' ', '_')}.png"
            )

            is_numeric = column_name in ["Level", "Score", "Kills", "Damage Done", "Gold Spent"]
            extracted_text = extract_text_from_image(cropped_cell, is_numeric=is_numeric)
            row_data.append(extracted_text)

        row_data.append(team)
        row_data.append(game_outcome)
        row_data.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        extracted_data.append(row_data)

    # Save current player data to file
    player_data_file = os.path.join(LAST_SESSION_FOLDER, "output.csv")
    save_to_csv(extracted_data, player_data_file, session_uuid)

    # Process middle control
    middle_control = config["middle_control"]
    middle_control_data = process_middle_control(cropped_image_pil, middle_control, LAST_SESSION_FOLDER, session_uuid)
    middle_control_file = os.path.join(LAST_SESSION_FOLDER, "middle_control.csv")
    save_middle_control_to_csv(middle_control_data, middle_control_file)

    # Aggregate data
    append_to_aggregate(os.path.join(DATA_FOLDER, "aggregate_player_data.csv"), player_data_file)
    append_to_aggregate(os.path.join(DATA_FOLDER, "aggregate_middle_control.csv"), middle_control_file)

    print(f"Session UUID: {session_uuid}")
    return extracted_data
