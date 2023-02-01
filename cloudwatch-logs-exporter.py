import sys
import time
import argparse
import re
import json
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError


def convert_to_datetime(str_dtime: str) -> datetime:
    return datetime.strptime(str_dtime, '%Y/%m/%d %H:%M:%S')


def convert_to_milliseconds(dtime: datetime) -> int:
    return int(dtime.timestamp()) * 1000


def normalize_prefix(prefix: str) -> str:
    if prefix[0] == '/':
        prefix = prefix[1:]

    if not prefix[-1] == '/':
        prefix = prefix + '/'

    prefix = re.sub(r'/{2,}', '/', prefix)

    return prefix


def generate_from_time(start_time: datetime, end_time: datetime):
    t = start_time
    while t <= end_time:
        yield t
        t += timedelta(days=1)


def print_task_status():
    print(f'taskName: {task_name}, taskStatus: {task_status}')


parser = argparse.ArgumentParser()
parser.add_argument('--start_datetime', required=True, type=convert_to_datetime,
                    help='Export logs from the time specified by this argument. It should be in the following format: "YYYY/mm/dd HH:MM:SS"')
parser.add_argument('--end_datetime', required=True, type=convert_to_datetime,
                    help='Export logs up to the time specified by this argument. It should be in the following format: "YYYY/mm/dd HH:MM:SS"')
parser.add_argument('--log_group_name', required=True, type=str,
                    help='Target log group name.')
parser.add_argument('--log_stream_name_prefix', required=True, type=normalize_prefix,
                    help='Log stream name prefix. Only log streams matching the given prefix will be exported.')
parser.add_argument('--destination_bucket', required=True, type=str,
                    help='S3 bucket name. Export logs to the S3 bucket specified in this argument.')
parser.add_argument('--destination_prefix', required=True, type=normalize_prefix,
                    help='S3 object prefix. Exported logs will have the prefix given to this argument.')
parser.add_argument('--profile', type=str,
                    help='aws profile name. This argument is optional.')
args = parser.parse_args()

session = boto3.Session(profile_name=args.profile)
logs = session.client('logs')

for from_time in generate_from_time(args.start_datetime, args.end_datetime):
    to_time = from_time + timedelta(seconds=86399)

    try:
        create_export_task_resp = logs.create_export_task(
            taskName=f'export_logs_from_{from_time.strftime("%Y-%m-%d_%H:%M:%S")}_to_{to_time.strftime("%Y-%m-%d_%H:%M:%S")}',
            logGroupName=args.log_group_name,
            logStreamNamePrefix=args.log_stream_name_prefix,
            fromTime=convert_to_milliseconds(from_time),
            to=convert_to_milliseconds(to_time),
            destination=args.destination_bucket,
            destinationPrefix=f'{args.destination_prefix}{from_time.strftime("%Y/%m/%d")}'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidParameterException':
            print(f'No logs exist from {from_time} to {to_time}. Create a task to export logs for the next 1 day.')
        else:
            raise e
    else:
        while True:
            describe_export_tasks_resp = logs.describe_export_tasks(
                taskId=create_export_task_resp["taskId"]
            )
            task_status = describe_export_tasks_resp["exportTasks"][0]["status"]["code"]
            task_name = describe_export_tasks_resp["exportTasks"][0]["taskName"]

            if task_status == 'COMPLETED':
                print_task_status()
                break
            elif task_status == 'PENDING' or task_status == 'RUNNING':
                print_task_status()
                time.sleep(10)
            else:
                print_task_status()
                print(json.dumps(describe_export_tasks_resp["exportTasks"][0], indent=4))
                sys.exit(1)
