import winreg

class DriveMapper:
    def __init__(self):
        self.mounted_devices_path = r"SYSTEM\MountedDevices"
        self.mapping = {}  # { 'serial_number': 'Drive Letter' }

    def map_drives(self):
        """
        Reads HKLM\SYSTEM\MountedDevices to match Serial Numbers to Drive Letters.
        """
        print(f"[*] Scanning Drive Letters in: {self.mounted_devices_path}...")
        
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(reg, self.mounted_devices_path)
            
            # Iterate through all values in MountedDevices
            info = winreg.QueryInfoKey(key)
            for i in range(info[1]): # info[1] is number of values
                value_name, value_data, type_ = winreg.EnumValue(key, i)
                
                # We only care about Drive Letters (e.g., "\DosDevices\F:")
                if "\\DosDevices\\" in value_name:
                    drive_letter = value_name.split("\\")[-1] # Extract "F:"
                    
                    # The data is binary (REG_BINARY). We must decode it.
                    # USB devices usually have the serial number embedded in this binary blob.
                    try:
                        # Decode binary to text (UTF-16 Little Endian is standard for Windows Registry)
                        decoded_data = value_data.decode('utf-16-le', errors='ignore')
                        
                        # The decoded data looks like:
                        # "USBSTOR#Disk&Ven_SanDisk&Prod_Cruzer...#{GUID}"
                        # We just need to check if our Serial Numbers exist in this string.
                        
                        # Store the mapping: Key = Full Data String, Value = Drive Letter
                        # In the Correlator, we will check if "Serial" is IN "Full Data String"
                        self.mapping[decoded_data] = drive_letter
                        
                    except Exception:
                        continue # Not a readable string
                        
        except PermissionError:
            print("[-] ERROR: Access Denied to MountedDevices.")
        except Exception as e:
            print(f"[-] Drive Mapping Error: {e}")

        return self.mapping

    def find_drive_letter(self, serial_number):
        """
        Searches the loaded mapping for a specific serial number.
        """
        if not serial_number:
            return "Unknown"
            
        for registry_string, drive_letter in self.mapping.items():
            # Check if the serial number is hidden inside the registry binary string
            if serial_number in registry_string:
                return drive_letter
                
        return "Not Mounted"