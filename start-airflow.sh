export AIRFLOW_HOME="$(pwd)/airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/dags"
airflow webserver -D
airflow scheduler -D


# pkill -f "airflow webserver"
# pkill -f "airflow scheduler"
