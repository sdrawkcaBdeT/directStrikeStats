import os
import sys
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

# Determine base_path correctly
if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    base_path = os.path.dirname(sys.executable)
else:
    # Running in a normal Python environment
    base_path = os.path.dirname(os.path.abspath(__file__))

# Define DATA_FOLDER relative to base_path
DATA_FOLDER = os.path.join(base_path, "data")
LAST_SESSION_FOLDER = os.path.join(DATA_FOLDER, "last_session")

# Make sure data folders exist
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def process_screenshot(player_name):
    session_uuid = generate_uuid()

    clear_session_folder(LAST_SESSION_FOLDER)

    config = load_config()

    screenshot_path = os.path.join(LAST_SESSION_FOLDER, "screenshot.png")
    pyautogui.screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    # Open the screenshot image
    image = Image.open(screenshot_path)

    # Convert the screenshot to OpenCV format
    screenshot_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # List of template image filenames to try (you can add more as needed)
    template_filenames = [
        "team1_template_undead.png",
        "team1_template_nightelf.png",
        # "team1_template_human.png",
        # "team1_template_orc.png"
    ]

    threshold = 0.8  # Adjust as needed
    best_match_val = 0
    best_match_loc = None

    # Attempt to find the top-left corner using multiple templates
    for template_name in template_filenames:
        template_path = os.path.join(base_path, template_name)
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            print(f"Template file not found: {template_path}")
            continue

        # Perform template matching
        result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        print(f"Template '{template_name}' match value: {max_val}")
        if max_val > threshold and max_val > best_match_val:
            best_match_val = max_val
            best_match_loc = max_loc

    # Check if we found a suitable match
    if best_match_loc is None:
        print("Top-left corner not detected with any template. Ensure the templates match the screenshot.")
        return

    # Top-left corner of the matched region
    top_left = best_match_loc
    print(f"Top-left corner detected at: {top_left} with a score of {best_match_val}")

    # Crop the region starting from the detected top-left corner
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

        # Extract the columns as before
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
        
    # Adjust victory/defeat assignments based on the user's team
    if game_outcome in ["Victory", "Defeat"]:
        user_team = None
        # Find the user's team by locating their player name
        for row in extracted_data:
            if row[1] == player_name:
                user_team = row[7]  # 'Team 1' or 'Team 2'
                break

        if user_team is not None:
            user_result = game_outcome
            opposing_result = "Defeat" if game_outcome == "Victory" else "Victory"

            # Assign outcomes based on the user's team
            for row in extracted_data:
                if row[7] == user_team:
                    row[8] = user_result
                else:
                    row[8] = opposing_result

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
