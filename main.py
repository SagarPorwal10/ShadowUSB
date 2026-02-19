import sys
import ctypes
import hashlib
from core.scanner import USBScanner
from core.log_parser import LogParser
from core.user_tracker import UserTracker
from core.drive_mapper import DriveMapper # <-- NEW
from core.correlator import Correlator
from reports.csv_exporter import CSVExporter
from reports.excel_exporter import ExcelExporter

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def calculate_file_hash(filename):
    """Calculates SHA-256 hash of the evidence file for Chain of Custody."""
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        # Read file in chunks to avoid memory issues
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    if not is_admin():
        print("[!] CRITICAL: Admin privileges required.")
        sys.exit(1)

    print("=== USB Forensics Tool v5.0 (Ultimate Edition) ===")
    
    # --- 1. GATHER ---
    print("\n[*] Phase 1: Scanning Registry...")
    scanner = USBScanner()
    raw_devices = scanner.scan()
    serials = [d['serial_number'] for d in raw_devices if d.get('serial_number')]
    
    print("[*] Phase 2: Parsing Timestamps...")
    parser = LogParser()
    timestamps = parser.parse_setupapi(serials)
    
    print("[*] Phase 3: Tracking Users (Online & Offline)...")
    tracker = UserTracker()
    # Trigger the full scan (Active + NTUSER.DAT files)
    full_user_map = tracker.scan_all_users(serials)
    
    # Pass this map directly to the Correlator
    user_map = full_user_map

    print("[*] Phase 4: Mapping Drive Letters...")
    mapper = DriveMapper()
    mapper.map_drives() # Pre-load the registry map

    # --- 2. CORRELATE ---
    print("[*] Phase 5: Correlating All Artifacts...")
    # Inject mapper into correlator
    correlator = Correlator(raw_devices, timestamps, user_map, mapper)
    canonical_data = correlator.correlate()
    
    print(f"[+] Correlation complete. {len(canonical_data)} unique events found.")

    # --- 3. REPORT & HASH ---
    print("\n[>] Generating Evidence Reports...")
    
    # CSV
    csv_file = "evidence_usb.csv"
    CSVExporter().export(canonical_data, csv_file)
    csv_hash = calculate_file_hash(csv_file)
    print(f"    [SHA-256]: {csv_hash}")
    
    # Excel
    xlsx_file = "evidence_usb.xlsx"
    ExcelExporter().export(canonical_data, xlsx_file)
    xlsx_hash = calculate_file_hash(xlsx_file)
    print(f"    [SHA-256]: {xlsx_hash}")

    print("\n[+] CHAIN OF CUSTODY LOG:")
    print(f"    Evidence 1: {csv_file} | Hash: {csv_hash[:20]}...")
    print(f"    Evidence 2: {xlsx_file} | Hash: {xlsx_hash[:20]}...")

if __name__ == "__main__":
    main()