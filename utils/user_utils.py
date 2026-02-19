import winreg
import ctypes
import ctypes.wintypes

def sid_to_username(sid_string):
    """
    Converts a Windows Security ID (SID) string to a username.
    """
    # Filter out system keys that aren't real users
    if len(sid_string) < 10 or "Classes" in sid_string:
        return None

    try:
        # We use the Windows API (advapi32) to lookup the account name
        sid = ctypes.create_unicode_buffer(sid_string)
        # (This is a simplified wrapper. For a robust tool, we'd use 
        # win32security from pywin32, but let's stick to stdlib logic where possible)
        
        # A simpler trick: Check the ProfileList in Registry
        key_path = f"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{sid_string}"
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(reg, key_path)
        profile_path, _ = winreg.QueryValueEx(key, "ProfileImagePath")
        
        # usually returns "C:\Users\Sagar" -> we extract "Sagar"
        username = profile_path.split("\\")[-1]
        return username

    except FileNotFoundError:
        return None  # SID exists but no profile (maybe a system account)
    except Exception:
        return sid_string  # Return the SID if resolution fails