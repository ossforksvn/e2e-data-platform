from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

import logging
from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
from airflow.utils.state import State


def _construct_message(context):
    """
    Constructs a Slack message using the context from an Airflow task.

    Args:
        context (dict): The context dictionary from an Airflow task.

    Returns:
        str: The constructed Slack message.
    """
    task_instance = context.get("task_instance")
    failed_tasks = [
        ti.task_id
        for ti in task_instance.get_dagrun().get_task_instances()
        if ti.state == State.FAILED
    ]
    failed_tasks_list = " ".join([f"`{task}`" for task in failed_tasks])


    msg = """
    :red_circle: *FAILURE ALERT*

    - *Dag*: {dag}
    - *Failed Tasks*: {failed_tasks_list}
    - *Execution Date Time*: {exec_date}
    """.format(
        dag=task_instance.dag_id,
        exec_date=context.get("execution_date"),
        failed_tasks_list=failed_tasks_list,
    )

    return msg


def send_failure_alert(context: dict):
    """
    Sends a job failure alert to Slack using the provided context from an Airflow task.

    Args:
        context (dict): The context dictionary from an Airflow task.
    """
    try:
        slack_msg = _construct_message(context)
        SlackWebhookHook(http_conn_id="slack_conn_id", message=slack_msg).execute()
    except Exception as e:
        logging.error(f"Error while sending alert: {e}")

default_args = {
    'start_date': datetime(2024, 1, 1),
    'catchup': False
}

dag = DAG(
    'spark_submit_job_dag',
    default_args=default_args,
    schedule='@once',
)

spark_submit_task = SparkSubmitOperator(
    conn_id='spark_adw14',  # Connection ID defined in Airflow
    task_id='spark_submit_task',
    name='airflow-spark-job',
    application='/opt/airflow/dags/scripts/spark_scripts_sayhi.py',  # Path to your Python script on the Airflow server
    executor_cores=1,
    executor_memory='2g',
    driver_memory='1g',
    verbose=True,
    dag=dag,
)

spark_submit_task
