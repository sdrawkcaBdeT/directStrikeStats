# Game Data Extractor

## Overview
The Game Data Extractor is a lightweight application that takes a screenshot of your game, extracts post-game stats using OCR (Optical Character Recognition), and displays the data for analysis.

## Features
- Automatically detects and extracts team and player stats.
- Works on any monitor resolution.
- User-friendly GUI with minimal setup required.

## Installation
1. Download the executable file.
2. Run the program (no installation required).

## Usage
1. Launch the application.
2. Click "Take Screenshot and Extract Data."
3. View the extracted data in the console (GUI output coming soon!).

## Advanced Configuration
If needed, adjust the `config.json` file to fit your resolution:
- `team1_coords`: Percentage-based coordinates for the Team 1 section.
- `row_count`: Number of rows in the table.
- `row_height`: Height of each row as a percentage.
- `columns`: Column start and end percentages for each stat.

## Troubleshooting
- If no data is extracted, ensure that Tesseract OCR is included in the `tesseract/` folder and accessible.
- If the program crashes, check `app.log` for error details.
