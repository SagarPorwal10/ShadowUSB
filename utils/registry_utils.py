import winreg

class RegistryUtils:
    @staticmethod
    def get_hklm_connection():
        """Connects to HKEY_LOCAL_MACHINE."""
        try:
            return winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        except PermissionError:
            print("[-] ERROR: Access Denied. Please run as Administrator.")
            return None

    @staticmethod
    def get_value(key_handle, value_name):
        """Safely retrieves a value from a registry key."""
        try:
            value, _ = winreg.QueryValueEx(key_handle, value_name)
            return value
        except FileNotFoundError:
            return "N/A"
        except Exception as e:
            return f"Error: {str(e)}"