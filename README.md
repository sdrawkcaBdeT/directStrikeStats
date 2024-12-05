# DirectStrike Stats

## Overview
This tool extracts game data from screenshots using Tesseract OCR.

## Installation
No installation is required! Simply download the app and run it.

## Usage
1. Open the application.
2. Click "Take Screenshot and Extract Data."
3. View extracted text in the console.

## Troubleshooting
- Ensure the `tesseract/` folder contains `tesseract.exe` and the `tessdata` folder.
- If OCR fails, verify that the game screen is visible in the screenshot.

## Configuration
Modify `config.json` to adjust the extraction regions:
- `team1_coords`: Relative percentages for the team section.
- `columns`: Relative percentages for each stat column.
