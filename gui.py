import os
import sys
import csv
import json
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QTabWidget, QWidget, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QProgressBar,
    QComboBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

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
        self.setGeometry(100, 100, 1200, 800)

        # Load configuration
        self.config = load_config(CONFIG_FILE)
        self.player_name = self.config.get("player_name", "Default Player")

        # Ensure the data folder exists
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        # Attempt to load aggregate data
        self.aggregate_data = self.load_aggregate_data()

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

        self.setup_analytics_tab()
        self.tab_widget.addTab(self.analytics_tab, "Analytics")

        self.central_widget.setLayout(layout)

    def load_aggregate_data(self):
        # Load aggregate player data if it exists
        player_data_path = os.path.join(DATA_FOLDER, "aggregate_player_data.csv")
        if os.path.exists(player_data_path):
            try:
                df = pd.read_csv(player_data_path)
                return df
            except Exception as e:
                print(f"Error loading aggregate data: {e}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()

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

        open_aggregate_player_data_button = QPushButton("Open Data Folder")
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

    def setup_analytics_tab(self):
        """Set up the Analytics tab."""
        self.analytics_tab = QWidget()

        # Main layout for the analytics tab
        main_layout = QVBoxLayout()

        # Top section: Match selection
        match_selection_layout = QVBoxLayout()
        match_selection_layout.addWidget(QLabel("Select Match UUID:"))
        self.match_selector = QComboBox()
        match_selection_layout.addWidget(self.match_selector)

        if not self.aggregate_data.empty:
            matches = self.aggregate_data["uuid"].unique()
            for m in matches:
                self.match_selector.addItem(m)

        self.match_selector.currentIndexChanged.connect(self.update_analytics_view)
        main_layout.addLayout(match_selection_layout)

        # Create a horizontal layout for the three main sections:
        h_layout = QHBoxLayout()

        # Left section: Match Context & Comparison
        left_section = QVBoxLayout()
        self.match_context_label = QLabel("Match Context & Comparison:")
        self.match_context_table = QTableWidget()
        left_section.addWidget(self.match_context_label)
        left_section.addWidget(self.match_context_table)

        # Middle section: Lifetime Stats
        middle_section = QVBoxLayout()
        self.lifetime_label = QLabel("Lifetime Stats:")
        self.lifetime_table = QTableWidget()
        middle_section.addWidget(self.lifetime_label)
        middle_section.addWidget(self.lifetime_table)

        # Right section: Chart
        right_section = QVBoxLayout()
        self.chart_view = QChartView()
        right_section.addWidget(self.chart_view)

        # Add these three sections to the horizontal layout
        h_layout.addLayout(left_section)
        h_layout.addLayout(middle_section)
        h_layout.addLayout(right_section)

        # Set stretch factors to achieve 2/5, 2/5, 1/5 width distribution
        h_layout.setStretch(0, 2)  # left section 2/5
        h_layout.setStretch(1, 2)  # middle section 2/5
        h_layout.setStretch(2, 1)  # right section 1/5

        main_layout.addLayout(h_layout)
        self.analytics_tab.setLayout(main_layout)

        # Initialize analytics view if we have data
        if not self.aggregate_data.empty and len(self.match_selector) > 0:
            self.update_analytics_view()

    def update_analytics_view(self):
        """Update the analytics tab based on the selected match UUID."""
        if self.aggregate_data.empty:
            self.statusBar().showMessage("No aggregate data available.", 5000)
            self.clear_analytics_tables()
            return

        selected_uuid = self.match_selector.currentText()
        if not selected_uuid:
            self.clear_analytics_tables()
            return

        # Filter for the selected match
        match_df = self.aggregate_data[self.aggregate_data["uuid"] == selected_uuid]

        if match_df.empty:
            self.statusBar().showMessage("No data for this match.", 5000)
            self.clear_analytics_tables()
            return

        # Define numeric columns
        numeric_cols = ["score", "kills", "damage", "goldSpent"]
        match_df = match_df.copy()  # Ensure we're working on a copy
        for col in numeric_cols:
            match_df[col] = pd.to_numeric(match_df[col], errors='coerce').fillna(0)

        # Identify player's team
        player_rows = match_df[match_df["player"] == self.player_name]
        if player_rows.empty:
            # If player's not found in this match, assume Team 1
            player_team = "Team 1"
        else:
            player_team = player_rows["team"].iloc[0]

        # Separate teammates & opponents
        teammates_df = match_df[match_df["team"] == player_team]
        opponents_df = match_df[match_df["team"] != player_team]

        def assign_alias(df, exclude_player=False, prefix="Teammate"):
            df = df.sort_values(by="player")
            aliases = {}
            i = 1
            for p in df["player"].unique():
                if exclude_player and p == self.player_name:
                    continue
                aliases[p] = f"{prefix} {i}"
                i += 1
            return aliases

        teammate_aliases = assign_alias(teammates_df, exclude_player=True, prefix="Teammate")
        opponent_aliases = assign_alias(opponents_df, prefix="Opponent")

        def summarize_stats(group_df):
            return {
                "Total Score": group_df["score"].sum(),
                "Avg Score": group_df["score"].mean(),
                "Total Kills": group_df["kills"].sum(),
                "Avg Kills": group_df["kills"].mean(),
                "Total Damage": group_df["damage"].sum(),
                "Avg Damage": group_df["damage"].mean(),
                "Total Gold": group_df["goldSpent"].sum(),
                "Avg Gold": group_df["goldSpent"].mean()
            }

        # Entities
        entities = {}
        # Player
        entities[self.player_name] = summarize_stats(match_df[match_df["player"] == self.player_name])
        # Each teammate
        for p, alias in teammate_aliases.items():
            entities[alias] = summarize_stats(match_df[match_df["player"] == p])
        # Each opponent
        for p, alias in opponent_aliases.items():
            entities[alias] = summarize_stats(match_df[match_df["player"] == p])

        # Teammates (excluding player)
        non_player_teammates = teammates_df[teammates_df["player"] != self.player_name]
        if not non_player_teammates.empty:
            entities["Teammates"] = summarize_stats(non_player_teammates)

        # Whole team
        entities["Team"] = summarize_stats(teammates_df)
        # Opponents
        entities["Opponents"] = summarize_stats(opponents_df)

        # Fill match_context_table
        columns = ["Entity","Total Score","Avg Score","Total Kills","Avg Kills","Total Damage","Avg Damage","Total Gold","Avg Gold"]
        self.match_context_table.setColumnCount(len(columns))
        self.match_context_table.setHorizontalHeaderLabels(columns)
        self.match_context_table.setRowCount(len(entities))

        for i, (entity, stats_dict) in enumerate(entities.items()):
            row_data = [
                entity,
                stats_dict["Total Score"], f"{stats_dict['Avg Score']:.2f}",
                stats_dict["Total Kills"], f"{stats_dict['Avg Kills']:.2f}",
                stats_dict["Total Damage"], f"{stats_dict['Avg Damage']:.2f}",
                stats_dict["Total Gold"], f"{stats_dict['Avg Gold']:.2f}"
            ]
            for j, val in enumerate(row_data):
                self.match_context_table.setItem(i, j, QTableWidgetItem(str(val)))

        self.match_context_table.resizeColumnsToContents()

        # Lifetime stats
        if not self.aggregate_data.empty:
            lifetime_df = self.aggregate_data.copy()
            for col in numeric_cols:
                lifetime_df[col] = pd.to_numeric(lifetime_df[col], errors='coerce').fillna(0)

            lifetime_summary = lifetime_df.groupby("player").agg(
                TotalScore=("score","sum"),
                AvgScore=("score","mean"),
                TotalKills=("kills","sum"),
                AvgKills=("kills","mean"),
                TotalDamage=("damage","sum"),
                AvgDamage=("damage","mean"),
                TotalGold=("goldSpent","sum"),
                AvgGold=("goldSpent","mean"),
                GamesPlayed=("uuid","nunique")
            ).reset_index().sort_values("TotalScore", ascending=False)

            lifetime_cols = ["Player","GamesPlayed","TotalScore","AvgScore","TotalKills","AvgKills","TotalDamage","AvgDamage","TotalGold","AvgGold"]
            self.lifetime_table.setColumnCount(len(lifetime_cols))
            self.lifetime_table.setHorizontalHeaderLabels(lifetime_cols)
            self.lifetime_table.setRowCount(len(lifetime_summary))
            for idx, row in lifetime_summary.iterrows():
                row_values = [
                    row["player"],
                    row["GamesPlayed"],
                    row["TotalScore"], f"{row['AvgScore']:.2f}",
                    row["TotalKills"], f"{row['AvgKills']:.2f}",
                    row["TotalDamage"], f"{row['AvgDamage']:.2f}",
                    row["TotalGold"], f"{row['AvgGold']:.2f}"
                ]
                for j, val in enumerate(row_values):
                    self.lifetime_table.setItem(idx, j, QTableWidgetItem(str(val)))
            self.lifetime_table.resizeColumnsToContents()

        # Chart: Player vs Team vs Opponents Avg Score in this match
        if "Team" in entities and "Opponents" in entities and self.player_name in entities:
            player_avg_score = entities[self.player_name]["Avg Score"]
            team_avg_score = entities["Team"]["Avg Score"]
            opp_avg_score = entities["Opponents"]["Avg Score"]

            chart = QChart()
            chart.setTitle("Average Score Comparison (This Match)")

            series = QBarSeries()
            player_set = QBarSet("Player")
            team_set = QBarSet("Team")
            opp_set = QBarSet("Opponents")

            player_set << player_avg_score
            team_set << team_avg_score
            opp_set << opp_avg_score

            series.append(player_set)
            series.append(team_set)
            series.append(opp_set)

            chart.addSeries(series)

            categories = ["Avg Score"]
            axisX = QBarCategoryAxis()
            axisX.append(categories)
            chart.addAxis(axisX, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axisX)

            axisY = QValueAxis()
            axisY.setRange(0, max(player_avg_score, team_avg_score, opp_avg_score) * 1.2)
            chart.addAxis(axisY, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axisY)

            self.chart_view.setChart(chart)
            self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        else:
            # Clear chart if something is missing
            self.chart_view.setChart(QChart())

    def clear_analytics_tables(self):
        self.match_context_table.setRowCount(0)
        self.lifetime_table.setRowCount(0)
        self.chart_view.setChart(QChart())

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
            self.player_name = updated_player_name
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
            extracted_data = process_screenshot(self.player_name)
            self.statusBar().showMessage("Screenshot processed successfully!", 5000)
            self.progress_bar.setValue(100)
            self.load_latest_game_data()

            # Reload aggregate data
            self.aggregate_data = self.load_aggregate_data()
            self.update_analytics_view()
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
