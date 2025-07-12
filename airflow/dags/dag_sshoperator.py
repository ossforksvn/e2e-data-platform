from airflow import DAG
from datetime import datetime
from airflow.providers.ssh.operators.ssh import SSHOperator

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
    'ssh_spark_submit_job_dag',
    default_args=default_args,
    schedule_interval='@once',
)


ssh_command = '''
docker exec e2e-data-platform-spark-master bash -c 'spark-submit \
    --master spark://spark-master:7077 \
    --executor-cores 1 \
    --executor-memory 1g \
    --driver-cores 1 \
    --driver-memory 1g \
    /opt/spark-apps/spark_apps_sayhi.py'
'''
ssh_spark_submit_task = SSHOperator(
    ssh_conn_id='ssh_spark_adw14',
    task_id='ssh_spark_submit_task',
    command=ssh_command,
    dag=dag,
)

ssh_spark_submit_task
