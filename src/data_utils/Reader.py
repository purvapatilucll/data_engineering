import os
import pandas as pd

class Reader:
    def __init__(self, subfolder):
        base_input = os.path.abspath("input")
        self.folder_path = os.path.join(base_input, subfolder)

    def read_batching_files(self):
        data = {}
        for file in os.listdir(self.folder_path):
            if file.endswith(".csv"):
                try:
                    df = pd.read_csv(os.path.join(self.folder_path, file))
                    data[file] = df
                    print(f"✅ Read: {file}")
                    data[file] = df
                except Exception as e:
                    print(f"❌ Failed to read {file}: {e}")
        return data

    def read_realtime_file(self, filename):
        path = os.path.join(self.folder_path, filename)
        try:
            df = pd.read_csv(path)
            print(f"✅ Read: {filename}")
            return df
        except Exception as e:
            print(f"❌ Failed to read {filename}: {e}")
            return None
