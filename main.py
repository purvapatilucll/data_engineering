from src.data_utils.Reader import Reader
# from src.data_utils.Writer import Writer
from src.data_utils.WriterAzure import Writer
from src.batch_processing.NashvilleValidator import PreProcessorValidator, PostProcessorValidator
from src.batch_processing.NashvilleProcessor import NashvilleProcessor

def batch_main():
    batch_reader = Reader("batch")
    writer = Writer()

    # get all data from the batch folder
    batch_data = batch_reader.read_batching_files()

    error_log = {}

    for filename, raw_df in batch_data.items():
        print(f"Processing file: {filename}")
        error_log[filename] = {}

        try:
            #Pre-processing validation (only print error info, not stop processing)
            pre_validator = PreProcessorValidator(raw_df)
            pre_validator.run_all_validations()

            if pre_validator.errors:
                error_log[filename]["pre_validation"] = pre_validator.errors
                print("⚠️ Pre-validation failed:")
                for e in pre_validator.errors:
                        print(f"  - {e}")
            else:
                print(" Pre-validation passed")

            # Data processing (cleaning / transformation)
            processor = NashvilleProcessor(raw_df)
            processed_df = processor.run_all_processors().get_processed_data()

            # Post-processing validation
            post_validator = PostProcessorValidator(processed_df)
            post_validator.run_all_validations()

            if post_validator.errors:
                error_log[filename]["post_validation"] = post_validator.errors
                print(" Post-validation failed (processed data still invalid):")
                for e in post_validator.errors:
                    print(f"  - {e}")
            else:
                print(" Post-validation passed")

            # Save output if post-validation passed
            if not post_validator.errors:
                writer.write_file(filename, processed_df)
                print(" File saved successfully")
                if filename in error_log:
                    del error_log[filename]

        except Exception as e:
            error_log[filename]["exception"] = str(e)
            print(f" Failed to process {filename}. Error: {e}")

    success_count = len(batch_data) - len(error_log)
    print(f"\n=== batch process summary ===")
    print(f"process file successfully: {success_count}/{len(batch_data)}")

if __name__ == "__main__":
    batch_main()
