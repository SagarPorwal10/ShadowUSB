import winreg
from utils.registry_utils import RegistryUtils

class USBScanner:
    def __init__(self):
        self.usbstor_path = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
        self.results = []

    def scan(self):
        """Scans the Registry for USB storage history."""
        print(f"[*] Scanning Registry path: HKLM\\{self.usbstor_path}...")
        
        reg_conn = RegistryUtils.get_hklm_connection()
        if not reg_conn:
            return []

        try:
            # Open the main USBSTOR key
            main_key = winreg.OpenKey(reg_conn, self.usbstor_path)
            
            # Loop 1: Iterate through unique Device IDs (e.g., Disk&Ven_Sandisk...)
            info = winreg.QueryInfoKey(main_key)
            for i in range(info[0]):
                device_id_name = winreg.EnumKey(main_key, i)
                device_id_path = f"{self.usbstor_path}\\{device_id_name}"
                
                # Open the Device ID key
                device_id_key = winreg.OpenKey(reg_conn, device_id_path)
                
                # Loop 2: Iterate through Serial Numbers (Instances of that device)
                sub_info = winreg.QueryInfoKey(device_id_key)
                for j in range(sub_info[0]):
                    serial_number = winreg.EnumKey(device_id_key, j)
                    final_path = f"{device_id_path}\\{serial_number}"
                    
                    # Open the specific Serial Number key to get details
                    final_key = winreg.OpenKey(reg_conn, final_path)
                    
                    # Extract Data
                    friendly_name = RegistryUtils.get_value(final_key, "FriendlyName")
                    hardware_id = RegistryUtils.get_value(final_key, "HardwareID")
                    
                    # Store structured data
                    self.results.append({
                        "device_name": friendly_name,
                        "serial_number": serial_number,
                        "device_id": device_id_name,
                        "registry_path": final_path,
                        "hardware_id": hardware_id if isinstance(hardware_id, list) else [hardware_id]
                    })
                    
        except FileNotFoundError:
            print("[-] USBSTOR Registry key not found. Is this a Windows machine?")
        except Exception as e:
            print(f"[-] specific error during scan: {e}")

        return self.results