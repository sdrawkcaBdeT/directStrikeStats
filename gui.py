import os
import sys
import csv
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTabWidget, QWidget, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from main import process_screenshot
from utils import load_config

CONFIG_FILE = "config.json"
# Get the directory of the current file (gui.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Construct an absolute path to the data folder
DATA_FOLDER = os.path.join(BASE_DIR, "data")
LAST_SESSION_FOLDER = os.path.join(DATA_FOLDER, "last_session")

class GameStatsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Stats Tracker")
        self.setGeometry(100, 100, 800, 600)

        # Load configuration
        self.config = load_config(CONFIG_FILE)

        # Ensure the data folder exists
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        # Central widget with tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Add tabs
        self.setup_game_stats_tab()
        self.tab_widget.addTab(self.game_stats_tab, "Game Stats")

        self.setup_config_tab()
        self.tab_widget.addTab(self.config_tab, "Configuration")

        self.setup_file_management_tab()
        self.tab_widget.addTab(self.file_management_tab, "File Management")

        self.central_widget.setLayout(layout)

    def setup_game_stats_tab(self):
        """Set up the Game Stats tab."""
        self.game_stats_tab = QWidget()
        layout = QVBoxLayout()

        # Screenshot Button
        self.screenshot_button = QPushButton("Click to Save Game Data!")
        self.screenshot_button.clicked.connect(self.take_screenshot)
        layout.addWidget(self.screenshot_button)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Latest Game Table
        self.latest_game_label = QLabel("Latest Game Data:")
        self.latest_game_table = QTableWidget(0, 11)
        self.latest_game_table.setHorizontalHeaderLabels(
            ["UUID", "Row", "Player", "Level", "Score", "Kills", "Damage", "Gold Spent", "Team", "Victory/Defeat", "Datetime"]
        )
        layout.addWidget(self.latest_game_label)
        layout.addWidget(self.latest_game_table)

        self.game_stats_tab.setLayout(layout)

        # Load the latest game data (if any)
        self.load_latest_game_data()

    def setup_config_tab(self):
        """Set up the Configuration tab."""
        self.config_tab = QWidget()
        layout = QVBoxLayout()

        player_name_label = QLabel("Set your player name for tracking purposes (case-sensitive):")
        self.player_name_input = QLineEdit()
        self.player_name_input.setText(self.config.get("player_name", "Default Player"))

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_player_name)

        layout.addWidget(player_name_label)
        layout.addWidget(self.player_name_input)
        layout.addWidget(save_button)

        self.config_tab.setLayout(layout)

    def setup_file_management_tab(self):
        """Set up the File Management tab."""
        self.file_management_tab = QWidget()
        layout = QVBoxLayout()

        open_aggregate_player_data_button = QPushButton("Open Aggregate Player Data")
        open_aggregate_player_data_button.clicked.connect(
            lambda: self.open_folder(DATA_FOLDER)
        )
        layout.addWidget(open_aggregate_player_data_button)

        open_aggregate_middle_control_button = QPushButton("Open Aggregate Middle Control")
        open_aggregate_middle_control_button.clicked.connect(
            lambda: self.open_file(os.path.join(DATA_FOLDER, "aggregate_middle_control.csv"))
        )
        layout.addWidget(open_aggregate_middle_control_button)

        open_session_folder_button = QPushButton("Open Last Session Folder")
        open_session_folder_button.clicked.connect(
            lambda: self.open_folder(LAST_SESSION_FOLDER)
        )
        layout.addWidget(open_session_folder_button)

        self.file_management_tab.setLayout(layout)

    def load_latest_game_data(self):
        """Load the latest game data into the game stats table."""
        try:
            latest_data_file = os.path.join(LAST_SESSION_FOLDER, "output.csv")
            if not os.path.exists(latest_data_file):
                self.statusBar().showMessage("No latest game data found.", 5000)
                return

            with open(latest_data_file, "r") as file:
                reader = csv.reader(file)
                headers = next(reader, None)
                self.latest_game_table.setRowCount(0)  # Clear existing rows
                if headers:
                    # The table already has headers set, so ignore CSV headers
                    pass

                for row_data in reader:
                    row_idx = self.latest_game_table.rowCount()
                    self.latest_game_table.insertRow(row_idx)
                    for col_idx, cell_data in enumerate(row_data):
                        self.latest_game_table.setItem(row_idx, col_idx, QTableWidgetItem(cell_data))

            self.statusBar().showMessage("Latest game data loaded successfully.", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"Error loading latest game data: {e}", 5000)

    def save_player_name(self):
        """Save the updated player name to the configuration."""
        updated_player_name = self.player_name_input.text().strip()
        if updated_player_name:
            self.config["player_name"] = updated_player_name
            with open(CONFIG_FILE, "w") as file:
                json.dump(self.config, file, indent=4)
            self.statusBar().showMessage(f"Player name updated to '{updated_player_name}'", 5000)
        else:
            self.statusBar().showMessage("Player name cannot be empty!", 5000)

    def take_screenshot(self):
        """Trigger the screenshot process."""
        self.statusBar().showMessage("Processing screenshot...")
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        try:
            # Process screenshot and data
            extracted_data = process_screenshot(self.config["player_name"])
            self.statusBar().showMessage("Screenshot processed successfully!", 5000)
            self.progress_bar.setValue(100)
            self.load_latest_game_data()
        except Exception as e:
            self.statusBar().showMessage(f"Error: {e}", 5000)
            self.progress_bar.setValue(0)

    def open_file(self, file_path):
        if os.path.exists(file_path):
            os.startfile(file_path)
        else:
            self.statusBar().showMessage(f"File not found: {file_path}", 5000)

    def open_folder(self, folder_path):
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            self.statusBar().showMessage(f"Folder not found: {folder_path}", 5000)

def run_gui():
    app = QApplication(sys.argv)
    window = GameStatsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_gui()
