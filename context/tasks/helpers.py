import os
from datetime import datetime
import pathlib


def get_stage_log_path(stage, context_log_path):
    return os.path.join(context_log_path, f'{stage}.log')


def write_log(context, stage, message, override=False):
    logs_path = os.path.join(context.context_folder, 'logs')
    log_file = get_stage_log_path(stage, logs_path)
    now = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    if os.path.exists(log_file):
        mode = 'w' if override else 'a'
        with open(log_file, mode) as f:
            f.write(f'[{now}] {message}\n')
    else:
        os.makedirs(pathlib.Path(log_file).parent.absolute(), exist_ok=True)
        with open(log_file, 'w') as f:
            f.write(f'[{now}] {message}\n')


def read_log(context, stage):
    logs_path = os.path.join(context.context_folder, 'logs')
    log_file = get_stage_log_path(stage, logs_path)
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            return f.readlines()
    else:
        return None


def change_status(status, context, stage, message, override=False):
    context.status = status
    context.save()
    write_log(context, stage, message, override)
