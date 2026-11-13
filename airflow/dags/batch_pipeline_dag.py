import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Path setting
DAGS_DIR = Path(__file__).parent  # /DE_project/dags/
PROJECT_ROOT = DAGS_DIR.parent  # /DE_project/
sys.path.append(str(PROJECT_ROOT))

from src.data_utils.Reader import Reader
from src.data_utils.Writer import Writer
from src.batch_processing.NashvilleValidator import PreProcessorValidator, PostProcessorValidator
from src.batch_processing.NashvilleProcessor import NashvilleProcessor

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(seconds=5),
}

dag = DAG(
    dag_id='batch_processing_pipeline',
    default_args=default_args,
    description='Data processing pipeline with validation steps',
    start_date=datetime(2025, 5, 9),
    schedule='@hourly',
    catchup=False
)


def load_batch_files(**kwargs):
    # switch to root
    os.chdir(PROJECT_ROOT)

    reader = Reader("batch")
    files = reader.read_batching_files()
    ti = kwargs['ti']
    ti.xcom_push(key='files', value=files)
    print(f"Loaded {len(files)} files.")


def validate_pre(**kwargs):
    ti = kwargs['ti']
    files = ti.xcom_pull(task_ids='load_batch_files', key='files')
    error_log = {}
    for fname, df in files.items():
        validator = PreProcessorValidator(df)
        validator.run_all_validations()
        if validator.errors:
            error_log[fname] = validator.errors
    ti.xcom_push(key='pre_errors', value=error_log)


def process_data(**kwargs):
    ti = kwargs['ti']
    files = ti.xcom_pull(task_ids='load_batch_files', key='files')
    processed = {}
    for fname, df in files.items():
        processor = NashvilleProcessor(df)
        result = processor.run_all_processors().get_processed_data()
        processed[fname] = result
    ti.xcom_push(key='processed', value=processed)


def validate_post(**kwargs):
    ti = kwargs['ti']
    processed = ti.xcom_pull(task_ids='process_data', key='processed')
    post_errors = {}
    for fname, df in processed.items():
        validator = PostProcessorValidator(df)
        validator.run_all_validations()
        if validator.errors:
            post_errors[fname] = validator.errors
    ti.xcom_push(key='post_errors', value=post_errors)


def save_cleaned_data(**kwargs):
    # switch to root
    os.chdir(PROJECT_ROOT)

    writer = Writer()
    ti = kwargs['ti']
    processed = ti.xcom_pull(task_ids='process_data', key='processed')
    post_errors = ti.xcom_pull(task_ids='validate_post', key='post_errors')

    for fname, df in processed.items():
        if fname not in post_errors:
            writer.write_file(fname, df)
            print(f"✅ Saved: {fname}")


load = PythonOperator(task_id='load_batch_files', python_callable=load_batch_files, dag=dag)
pre_val = PythonOperator(task_id='validate_pre', python_callable=validate_pre, dag=dag)
process = PythonOperator(task_id='process_data', python_callable=process_data, dag=dag)
post_val = PythonOperator(task_id='validate_post', python_callable=validate_post, dag=dag)
save = PythonOperator(task_id='save_cleaned_data', python_callable=save_cleaned_data, dag=dag)

load >> pre_val >> process >> post_val >> save