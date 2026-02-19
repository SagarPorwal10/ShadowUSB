import csv
import os

class CSVExporter:
    def export(self, data, filename="usb_forensics_report.csv"):
        if not data:
            print("[-] No data to export.")
            return

        keys = data[0].keys()
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(data)
            print(f"[+] CSV Report generated: {os.path.abspath(filename)}")
        except IOError as e:
            print(f"[-] Error writing CSV: {e}")