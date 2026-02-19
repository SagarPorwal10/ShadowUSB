import os
import re
from datetime import datetime

class LogParser:
    def __init__(self):
        # Standard location for Windows Setup API log
        self.log_path = r"C:\Windows\INF\setupapi.dev.log"
        self.found_dates = {}  # Format: { 'serial_number': 'min_date_string' }

    def parse_setupapi(self, target_serials):
        """
        Scans the setupapi.dev.log for the first installation date 
        of the given serial numbers.
        """
        print(f"[*] Parsing log file: {self.log_path}...")
        
        if not os.path.exists(self.log_path):
            print("[-] ERROR: setupapi.dev.log not found.")
            return {}

        # Regex to capture the Section Start timestamp
        # Example line: >>>  Section start 2023/11/15 08:32:11.453
        timestamp_pattern = re.compile(r">>>  Section start (\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})")
        
        current_section_time = None

        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 1. Check for a new Timestamp Section
                    ts_match = timestamp_pattern.search(line)
                    if ts_match:
                        current_section_time = ts_match.group(1)
                        continue

                    # 2. If we are inside a valid section, look for Serial Numbers
                    if current_section_time:
                        for serial in target_serials:
                            if serial in line:
                                # We found a serial! Is this the *first* time we've seen it?
                                # Or is this timestamp older than what we already have?
                                self._update_earliest_date(serial, current_section_time)

        except PermissionError:
            print("[-] ERROR: Permission denied reading the log file.")
        except Exception as e:
            print(f"[-] ERROR parsing log: {e}")

        return self.found_dates

    def _update_earliest_date(self, serial, new_date_str):
        """Helper to keep only the oldest timestamp for a device."""
        # Convert string to datetime object for comparison
        new_date = datetime.strptime(new_date_str, "%Y/%m/%d %H:%M:%S")
        
        if serial not in self.found_dates:
            self.found_dates[serial] = new_date
        else:
            existing_date = self.found_dates[serial]
            if new_date < existing_date:
                self.found_dates[serial] = new_date