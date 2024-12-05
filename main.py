import os
import json
from PIL import Image
import pyautogui
import csv

# Toggle to enable or disable saving cropped images for testing
SAVE_CROPPED_IMAGES = True

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

# Extract text from cropped image (placeholder for OCR or manual testing)
def extract_text_from_image(cropped_image):
    # Placeholder for OCR or other logic; returning "TEST" for now
    return "TEST"

# Save extracted stats to CSV
def save_to_csv(data, output_file="output.csv"):
    with open(output_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Row", "Player Name", "Level", "Score", "Kills", "Damage Done", "Gold Spent"])  # Header
        writer.writerows(data)
    print(f"Data saved to {output_file}")

# Main function to process screenshot and export CSV
def process_screenshot():
    # Load the config
    config = load_config()

    # Take a screenshot
    screenshot_path = "screenshot.png"
    pyautogui.screenshot(screenshot_path)
    print(f"Screenshot saved: {screenshot_path}")

    # Open the screenshot image
    image = Image.open(screenshot_path)

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
                image,
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
            # Extract text (placeholder logic)
            extracted_text = extract_text_from_image(cropped_cell)
            row_data.append(extracted_text)
        extracted_data.append(row_data)

    # Process middle control for Team 1 and Team 2 (Optional)
    middle_control = config["middle_control"]
    for team, coords in middle_control.items():
        cropped_team_area = crop_area(
            image,
            coords["top_left_x"],
            coords["bottom_right_x"],
            coords["top_left_y"],
            coords["bottom_right_y"]
        )
        # Save the cropped image for debugging
        save_cropped_image(
            cropped_team_area,
            output_folder,
            f"Middle_Control_{team.replace(' ', '_')}.png"
        )
        print(f"Processed Middle Control for {team}")

    # Save all extracted data to a CSV
    save_to_csv(extracted_data)

# Example usage
if __name__ == "__main__":
    process_screenshot()
