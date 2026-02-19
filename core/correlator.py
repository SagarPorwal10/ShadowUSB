class Correlator:
    def __init__(self, scanner_results, log_dates, user_map, drive_mapping):
        self.scanner_results = scanner_results
        self.log_dates = log_dates
        self.user_map = user_map
        self.drive_mapping = drive_mapping  # <-- NEW: Inject the mapper

    def correlate(self):
        canonical_data = []

        for device in self.scanner_results:
            serial = device.get('serial_number')
            
            # 1. Existing Logic (Timestamps & Users)
            first_seen = self.log_dates.get(serial)
            first_seen_str = first_seen.strftime("%Y-%m-%d %H:%M:%S") if first_seen else "N/A"
            
            users = self.user_map.get(serial, [])
            users_str = ", ".join(users) if users else "System/Unknown"

            # 2. NEW: Find Drive Letter
            # "Did this USB mount as E: or F:?"
            drive_letter = self.drive_mapping.find_drive_letter(serial)

            entry = {
                "Device Name": device.get('device_name', 'Unknown'),
                "Serial Number": serial,
                "First Connected (Log)": first_seen_str,
                "Last Known Drive": drive_letter,   # <-- NEW COLUMN
                "Associated Users": users_str,
                "Vendor ID": device.get('device_id', '').split('&')[1] if '&' in device.get('device_id', '') else "N/A",
                "Raw Registry Path": device.get('registry_path')
            }
            
            canonical_data.append(entry)

        canonical_data.sort(key=lambda x: x['First Connected (Log)'] if x['First Connected (Log)'] != "N/A" else "0000", reverse=True)
        return canonical_data