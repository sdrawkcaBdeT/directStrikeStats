import os
import json
from PIL import Image

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

# Main function to demonstrate how to use rows, columns, and middle control
def process_image(image_path):
    # Load the config
    config = load_config()

    # Open the image
    image = Image.open(image_path)

    # Output folder for testing
    output_folder = "testing_output"

    # Crop and process each player row
    rows = config["rows"]
    columns = config["columns"]
    for i, row in enumerate(rows):
        print(f"Processing Row {i + 1}")
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
            # Example placeholder for processing (e.g., OCR or further analysis)
            print(f"Cropping {column_name} for Row {i + 1}")

    # Crop middle control for Team 1 and Team 2
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
        # Example placeholder for processing (e.g., OCR or further analysis)
        print(f"Cropping Middle Control for {team}")

# Example usage
if __name__ == "__main__":
    # Replace 'screenshot.png' with your image file path
    process_image("screenshot.png")
