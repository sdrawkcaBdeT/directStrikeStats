import os
import json
import csv
from PIL import Image
import pytesseract
import pyautogui
import keyboard
import cv2
import numpy as np
import uuid
import pandas as pd

# Toggle to enable or disable saving cropped images for testing
SAVE_CROPPED_IMAGES = True

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = os.path.join(os.getcwd(), "tesseract", "tesseract.exe")

# # Debugging the path
# print(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
# print(f"Does Tesseract exist? {os.path.exists(pytesseract.pytesseract.tesseract_cmd)}")

# Generate a UUID for the current screenshot session
def generate_uuid():
    return str(uuid.uuid4())

# Load configuration from JSON file
def load_config(config_file="config.json"):
    with open(config_file, "r") as f:
        return json.load(f)

# Example to crop areas dynamically using percentages
def crop_area(image, start_x, end_x, top_y, bottom_y):
    width, height = image.size
    return image.crop((
        int(start_x / 100 * width),
        int(top_y / 100 * height),
        int(end_x / 100 * width),
        int(bottom_y / 100 * height)
    ))

# Save cropped images for testing
def save_cropped_image(image, output_folder, file_name):
    if SAVE_CROPPED_IMAGES:
        os.makedirs(output_folder, exist_ok=True)  # Ensure the folder exists
        file_path = os.path.join(output_folder, file_name)
        image.save(file_path)
        print(f"Saved cropped image: {file_path}")

# Extract text from cropped image using Tesseract OCR
def extract_text_from_image(cropped_image, is_numeric=False):
    # Convert the image to grayscale for better OCR results
    gray_image = cropped_image.convert("L")

    # Use OCR to extract text
    config = "--psm 6"  # Treat the image as a single block of text
    if is_numeric:
        config += " outputbase digits"  # Optimize for numeric data

    extracted_text = pytesseract.image_to_string(gray_image, config=config).strip()
    return extracted_text

# Save extracted stats to CSV
def save_to_csv(data, output_file, uuid_str):
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["UUID", "Row", "Player Name", "Level", "Score", "Kills", "Damage Done", "Gold Spent"])  # Header
        for row in data:
            writer.writerow([uuid_str] + row)
    print(f"Data saved to {output_file}")

# Save middle control data to a separate file
def save_middle_control_to_csv(data, output_file, uuid_str):
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["UUID", "Team", "Top-Left X", "Top-Left Y", "Bottom-Right X", "Bottom-Right Y"])  # Header
        for team, coords in data.items():
            writer.writerow([
                uuid_str,
                team,
                coords["top_left_x"],
                coords["top_left_y"],
                coords["bottom_right_x"],
                coords["bottom_right_y"]
            ])
    print(f"Middle control data saved to {output_file}")

# Append new data to an aggregate file
def append_to_aggregate(data_file, new_data_file, is_middle_control=False):
    # Read existing aggregate data if available
    try:
        aggregate_data = pd.read_csv(data_file)
    except FileNotFoundError:
        aggregate_data = pd.DataFrame()

    # Read new data
    new_data = pd.read_csv(new_data_file)

    # Append new data to the aggregate
    aggregate_data = pd.concat([aggregate_data, new_data])

    # Save back to the aggregate file
    aggregate_data.to_csv(data_file, index=False)
    print(f"Data aggregated into {data_file}")

# Main function to process a screenshot
# Main function to process a screenshot
def process_screenshot():
    # Generate UUID for the session
    session_uuid = generate_uuid()

    # Load the config
    config = load_config()

    # Take a screenshot
    screenshot_path = "screenshot.png"
    pyautogui.screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    # Open the screenshot image
    image = Image.open(screenshot_path)

    # Convert the screenshot to a format compatible with OpenCV
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
    threshold = 0.8  # Adjust as needed based on template clarity
    if max_val < threshold:
        print("Top-left corner not detected. Ensure the template matches the screenshot.")
        return

    # Top-left corner of the matched region
    top_left = max_loc
    print(f"Top-left corner detected at: {top_left}")

    # Crop the region starting from the detected top-left corner
    cropped_image = screenshot_cv[
        top_left[1]:top_left[1] + int(915 / 1440 * screenshot_cv.shape[0]),  # Height
        top_left[0]:top_left[0] + int(1665 / 2560 * screenshot_cv.shape[1])  # Width
    ]

    # Convert cropped image back to PIL format for further processing
    cropped_image_pil = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))

    # Output folder for testing
    output_folder = "testing_output"

    # Process each player row and extract stats
    rows = config["rows"]
    columns = config["columns"]
    extracted_data = []  # Store extracted stats for CSV export

    for i, row in enumerate(rows):
        print(f"Processing Row {i + 1}")
        row_data = [f"Row {i + 1}"]  # Add row identifier
        for column_name, column_coords in columns.items():
            cropped_cell = crop_area(
                cropped_image_pil,
                column_coords["start_x"],
                column_coords["end_x"],
                row["top_y"],
                row["bottom_y"]
            )
            # Save the cropped image for debugging
            save_cropped_image(
                cropped_cell,
                output_folder,
                f"Row_{i + 1}_{column_name.replace(' ', '_')}.png"
            )
            # Extract text using OCR
            is_numeric = column_name in ["Level", "Score", "Kills", "Damage Done", "Gold Spent"]
            extracted_text = extract_text_from_image(cropped_cell, is_numeric=is_numeric)
            row_data.append(extracted_text)
        extracted_data.append(row_data)

    # Save current player data to file
    player_data_file = f"output_{session_uuid}.csv"
    save_to_csv(extracted_data, player_data_file, session_uuid)

    # Process middle control for Team 1 and Team 2
    middle_control = config["middle_control"]
    middle_control_file = f"middle_control_{session_uuid}.csv"
    save_middle_control_to_csv(middle_control, middle_control_file, session_uuid)

    # Aggregate data
    append_to_aggregate("aggregate_player_data.csv", player_data_file)
    append_to_aggregate("aggregate_middle_control.csv", middle_control_file, is_middle_control=True)

    print(f"Session UUID: {session_uuid}")
    
# Main program loop to listen for hotkey
def main():
    print("Press Ctrl+S to capture the scoreboard and process stats.")
    while True:
        if keyboard.is_pressed("ctrl+s"):
            print("Hotkey pressed: Capturing and processing scoreboard...")
            process_screenshot()
            print("Processing complete. Press Ctrl+S to capture again or close the program to exit.")
            # Wait until the key is released to avoid multiple triggers
            keyboard.wait("ctrl+s", suppress=True)

# Run the main program
if __name__ == "__main__":
    main()
