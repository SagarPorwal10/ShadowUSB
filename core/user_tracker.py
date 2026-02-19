import winreg
import os
from utils.user_utils import sid_to_username

class UserTracker:
    def __init__(self):
        # Maps Serial Number -> Set of Usernames
        # Example: { '123456': {'Sagar', 'Admin'} }
        self.device_user_map = {} 
        self.users_dir = r"C:\Users"

    def scan_all_users(self, target_serials):
        """
        Master function: Scans both Online (logged in) and Offline (disk) users.
        """
        print("[*] Tracking: Scanning currently logged-in users...")
        self._scan_online_users(target_serials)
        
        print("[*] Tracking: Scanning offline user hives (NTUSER.DAT)...")
        self._scan_offline_users(target_serials)
        
        return self.device_user_map

    def _scan_online_users(self, target_serials):
        """Scans HKEY_USERS for currently active sessions."""
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_USERS)
            info = winreg.QueryInfoKey(reg)
            
            for i in range(info[0]):
                sid = winreg.EnumKey(reg, i)
                if len(sid) < 20 or "Classes" in sid: continue # Skip system keys

                # Resolve Username
                username = sid_to_username(sid)
                if not username: continue
                
                # Scan this user's hive
                # Path: HKEY_USERS\<SID>\...
                self._check_hive_for_artifacts(winreg.HKEY_USERS, sid, username, target_serials)
                
        except Exception as e:
            print(f"[-] Error scanning online users: {e}")

    def _scan_offline_users(self, target_serials):
        """
        Loads NTUSER.DAT from disk for users who are NOT logged in.
        """
        # Get list of user folders
        try:
            user_folders = [f for f in os.listdir(self.users_dir) if os.path.isdir(os.path.join(self.users_dir, f))]
        except PermissionError:
            print("[-] Error: Cannot access C:\\Users. Run as Admin.")
            return

        for folder in user_folders:
            # Skip system folders
            if folder in ["Public", "Default", "Default User", "All Users"]: continue

            hive_path = os.path.join(self.users_dir, folder, "NTUSER.DAT")
            if not os.path.exists(hive_path): continue

            # Define a temporary key name to load this hive into
            temp_key_name = f"OFFLINE_{folder}"
            
            try:
                # 1. LOAD the hive into HKEY_USERS
                winreg.LoadKey(winreg.HKEY_USERS, temp_key_name, hive_path)
                
                # 2. SCAN the hive (just like an online user)
                self._check_hive_for_artifacts(winreg.HKEY_USERS, temp_key_name, folder, target_serials)
                
                # 3. UNLOAD the hive (Crucial! Otherwise the file remains locked)
                winreg.UnLoadKey(winreg.HKEY_USERS, temp_key_name)
                
            except OSError as e:
                # Common error: "The process cannot access the file because it is being used by another process"
                # This means the user is actually logged in, so we already scanned them in Step 1.
                if "used by another process" not in str(e):
                    print(f"[-] Could not load offline hive for {folder}: {e}")
            except Exception as e:
                print(f"[-] Error processing {folder}: {e}")
                # Try to force unload just in case
                try: winreg.UnLoadKey(winreg.HKEY_USERS, temp_key_name)
                except: pass

    def _check_hive_for_artifacts(self, hive_root, subkey_name, username, target_serials):
        """
        Helper: Looks for MountPoints2 in a specific hive key.
        """
        mountpoints_path = f"{subkey_name}\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\MountPoints2"
        
        try:
            reg = winreg.ConnectRegistry(None, hive_root)
            key = winreg.OpenKey(reg, mountpoints_path)
            
            # Get all subkeys (mounted devices)
            info = winreg.QueryInfoKey(key)
            mounted_devices = [winreg.EnumKey(key, i) for i in range(info[0])]
            
            # Check against our target serials
            for serial in target_serials:
                # Matches if the serial appears anywhere in the key name
                # Key format: ##?#USBSTOR#Disk&Ven_X&Prod_Y#<SERIAL>#{GUID}
                if any(serial in device_entry for device_entry in mounted_devices):
                    self._add_entry(serial, username)
                    
        except FileNotFoundError:
            return # User has no MountPoints2 key (never used external storage)
        except Exception:
            return

    def _add_entry(self, serial, username):
        if serial not in self.device_user_map:
            self.device_user_map[serial] = set()
        self.device_user_map[serial].add(username)

    def get_users_for_serial(self, serial):
        """Returns a list of users for a given serial."""
        return list(self.device_user_map.get(serial, []))