import pandas as pd
import os

class ExcelExporter:
    def export(self, data, filename="usb_forensics_report.xlsx"):
        if not data:
            return

        try:
            # Convert Canonical Data to DataFrame
            df = pd.DataFrame(data)
            
            # Create a Pandas Excel Writer using XlsxWriter as the engine
            writer = pd.ExcelWriter(filename, engine='openpyxl')
            
            # Write data to "Evidence" sheet
            df.to_excel(writer, sheet_name='Evidence', index=False)
            
            # Auto-adjust column widths (Basic styling)
            worksheet = writer.sheets['Evidence']
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

            writer.close()
            print(f"[+] Excel Report generated: {os.path.abspath(filename)}")
            
        except ImportError:
            print("[-] Error: 'pandas' or 'openpyxl' not installed. Run: pip install pandas openpyxl")
        except Exception as e:
            print(f"[-] Error writing Excel: {e}")