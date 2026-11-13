import os
import pandas as pd

class Writer:
    def __init__(self, output_folder="output"):
        self.output_folder = os.path.abspath(output_folder)
        os.makedirs(self.output_folder, exist_ok=True)

    def write_file(self, original_filename, processed_data):

        base_name = os.path.splitext(original_filename)[0]
                                        #  the output file is .xlsx
        file_path = os.path.join(self.output_folder, f"{base_name}_processed.xlsx")

        try:
            if isinstance(processed_data, dict):  # multiple sheet
                with pd.ExcelWriter(file_path) as writer:
                    for sheet_name, df in processed_data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:  # single sheet
                processed_data.to_excel(file_path, index=False)

            print(f" write succeed: {file_path}")
        except Exception as e:
            print(f" write failed: {file_path}，error：{e}")
