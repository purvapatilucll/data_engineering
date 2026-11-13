import os
import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

class Writer:
    def __init__(self, output_folder="output"):
        self.output_folder = os.path.abspath(output_folder)
        os.makedirs(self.output_folder, exist_ok=True)

        self.azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.azure_container_name = os.getenv("AZURE_CONTAINER_NAME")

        if self.azure_connection_string and self.azure_container_name:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.azure_connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.azure_container_name)

    def write_file(self, original_filename, processed_data):
        base_name = os.path.splitext(original_filename)[0]
        file_name = f"{base_name}_processed.xlsx"
        file_path = os.path.join(self.output_folder, file_name)

        try:
            if isinstance(processed_data, dict):
                with pd.ExcelWriter(file_path) as writer:
                    for sheet_name, df in processed_data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                processed_data.to_excel(file_path, index=False)

            print(f"✅ [LOCAL WRITE] File saved: {file_path}")

            if self.azure_connection_string and self.azure_container_name:
                self.upload_to_azure(file_path, file_name)

        except Exception as e:
            print(f"❌ [WRITE FAILED] {file_path}, Error: {e}")


    def upload_to_azure(self, local_path, blob_name):
        try:
            with open(local_path, "rb") as data:
                self.container_client.upload_blob(name=blob_name, data=data, overwrite=True)
            print(f"✅ [AZURE BLOB] Uploaded to {self.azure_container_name}/{blob_name}")
        except Exception as e:
            print(f"❌ [AZURE UPLOAD FAILED] Error uploading {blob_name}: {e}")
