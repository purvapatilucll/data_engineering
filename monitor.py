import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.data_utils.Reader import Reader
# from src.data_utils.Writer import Writer
from src.data_utils.WriterAzure import Writer
from src.realtime_processing.TripProcessor import TripProcessor
from src.realtime_processing.TripValidator import PreTripProcessorValidator, PostTripProcessorValidator


class RealtimeMonitor(FileSystemEventHandler):
    def __init__(self):
        self.target_filename = "Traveler_trip_details.csv"
        self.reader = Reader("realtime")
        self.writer = Writer()

        self.input_dir = os.path.abspath(self.reader.folder_path)
        self.processed_dir = os.path.join(self.input_dir, "processed")
        os.makedirs(self.processed_dir, exist_ok=True)

        print(f"Initializing monitor directory: {self.input_dir}")

        # Process an existing file on startup
        self._process_existing_file()

    # Handle a pre-existing target file at startup
    def _process_existing_file(self):

        target_path = os.path.join(self.input_dir, self.target_filename)
        if os.path.exists(target_path):
            print(f"🔍 Found existing target file, processing: {self.target_filename}")
            self._process_file(self.target_filename)

    def on_created(self, event):

        if (
                not event.is_directory
                and os.path.basename(event.src_path) == self.target_filename
        ):
            print(f"Detected new file: {self.target_filename}")
            time.sleep(0.3)
            self._process_file(self.target_filename)

    # reader + validator-processor + writer (and realtime file move to the processed folder)
    def _process_file(self, filename):
        src_path = os.path.join(self.input_dir, filename)

        try:
            print(f"Step 1/3: Reading file {filename}")
            raw_df = self.reader.read_realtime_file(filename)
            if raw_df is None:
                raise ValueError("File read failed")

            print("Step 2/3: Validating and processing data")
            processed_df = self._validate_and_process(raw_df, filename)

            print("Step 3/3: Saving results")
            self.writer.write_file(filename, processed_df)
            os.rename(src_path, os.path.join(self.processed_dir, filename))
            print(f"✅ Processing complete: {filename} -> Archived(processed folder)")

        except Exception as e:
            print(f"❌ Processing failed: {str(e)}")

    def _validate_and_process(self, df, filename):
        # Pre-validation
        pre_validator = PreTripProcessorValidator(df)
        pre_validator.run_all_validations()
        if pre_validator.errors:
            print(f"⚠️ Pre-validation warnings ({filename}):")
            for e in pre_validator.errors:
                print(f"  - {e}")

        # Data transformation
        processor = TripProcessor(df)
        processed_df = processor.run_all_processors().get_processed_data()

        # Post-validation
        post_validator = PostTripProcessorValidator(processed_df)
        post_validator.run_all_validations()
        if post_validator.errors:
            error_msg = "Post-validation failed:\n" + "\n".join(post_validator.errors)
            raise ValueError(error_msg)

        formatted_df = processor.format_cost_columns().get_processed_data()

        return formatted_df


def start_monitoring():
    observer = Observer()
    event_handler = RealtimeMonitor()
    observer.schedule(event_handler, path=event_handler.input_dir, recursive=False)
    observer.start()
    print(f" Monitoring started (exclusively for {event_handler.target_filename})")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_monitoring()