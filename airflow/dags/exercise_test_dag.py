from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def print_hello():
    print("Hello, Airflow!")

dag = DAG(
    'exercise_test',
    description='DAG with PythonOperator',
    schedule=None,
    start_date=datetime(2023,1,1),
    catchup=False
)

hello_task = PythonOperator(
    task_id='hello_task',
    python_callable=print_hello,
    dag=dag
)