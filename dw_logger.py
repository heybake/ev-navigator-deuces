"""
dw_logger.py
DATA PERSISTENCE LAYER
Handles all CSV file operations, directory management, and logging schema.
"""

import os
import csv
import datetime

class SessionLogger:
    """
    Manages the lifecycle of a simulation log file.
    """
    # CENTRALIZED SCHEMA: The Single Source of Truth for log columns
    FIELDNAMES = [
        "Hand_ID", "Variant", "Wheel_Mode", "Lines", "Denom", "Bankroll", 
        "Net_Result", "EV", "Wheel_Mult", "Wheel_Outer", "Wheel_Inner",
        "Hand_Dealt", "Held_Cards", "Action", "Wins", "Best_Hit", "Hit_Summary",
        "Amy_Win_Count", "Amy_Trigger", "Protocol_Trigger" 
    ]

    def __init__(self, variant, amy_active=False, protocol_active=False, session_idx=None):
        self.filepath = self._generate_filename(variant, amy_active, protocol_active, session_idx)
        self.file_handle = None
        self.writer = None
        self._initialize_file(session_idx)

    def _generate_filename(self, variant, amy_active, protocol_active, session_idx):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_tag = "_AMY" if amy_active else ""
        proto_tag = "_PROTO" if protocol_active else ""
        session_tag = f"_S{session_idx}" if session_idx is not None else ""
        
        return f"logs/session_{variant}{mode_tag}{proto_tag}{session_tag}_{timestamp}.csv"

    def _initialize_file(self, session_idx):
        self.file_handle = open(self.filepath, 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file_handle, fieldnames=self.FIELDNAMES)
        self.writer.writeheader()
        
        # Verbosity Control: Only print every 10th session in batch mode
        if session_idx is None or session_idx % 10 == 0:
            print(f"   📝 Log Started: {self.filepath}")

    def log(self, data_dict):
        """
        Writes a single row to the CSV.
        """
        if self.writer:
            self.writer.writerow(data_dict)

    def close(self):
        """
        Closes the file handle safely.
        """
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    def get_filepath(self):
        """Returns the path for plotting tools."""
        return self.filepath