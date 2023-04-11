from os import environ
import json
from arbiter import Arbiter
import requests


def get_vhost_queues(host: str, port: int, user: str, password: str, vhost: str, timeout: int) -> list:
    arbiter = Arbiter(
        host=host,
        port=int(port),
        user=user,
        password=password,
        vhost=vhost,
        timeout=int(timeout)
    )
    try:
        queues = list(arbiter.workers().keys())
        arbiter.close()
    except:
        queues = []
    return queues


def handler(event=None, context=None):
    debug_sleep = environ.get("debug_sleep")
    if debug_sleep:
        print('sleeping for', debug_sleep)
        try:
            from time import sleep
            sleep(int(debug_sleep))
        except ValueError:
            ...

    user = environ.get("rabbit_user")
    password = environ.get("rabbit_password")
    host = environ.get("rabbit_host")
    port = environ.get("rabbit_port", 5672)
    timeout = environ.get("AWS_LAMBDA_FUNCTION_TIMEOUT", 120)

    put_url = environ.get('put_url')
    project_ids_get_url = environ.get('project_ids_get_url')

    vhost_template = environ.get("vhost_template", 'project_{project_id}_vhost')
    core_vhost = environ.get("core_vhost", 'carrier')

    headers = {'content-type': 'application/json'}
    if environ.get("token"):
        headers['Authorization'] = f'{environ.get("token_type", "bearer")} {environ.get("token")}'

    try:
        port = int(port)
        timeout = int(timeout)
        if debug_sleep:
            print('getting queues for', core_vhost)
        all_queues = {
            core_vhost: get_vhost_queues(host, port, user, password, core_vhost, timeout)
        }
        if debug_sleep:
            print('got queues for', all_queues)
            print('getting project ids')
        project_ids = requests.patch(project_ids_get_url, headers=headers).json()
        if debug_sleep:
            print('got project ids:', project_ids)

        for i in project_ids:
            vhost = vhost_template.format(project_id=i)
            if debug_sleep:
                print('getting queues for', vhost)
            queues = get_vhost_queues(host, port, user, password, vhost, timeout)
            all_queues[vhost] = queues
            if debug_sleep:
                print('got queues for', vhost, ' ', queues)

        requests.put(put_url, json=all_queues, headers=headers)

    except Exception as e:
        if debug_sleep:
            print(e)
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    return {
        'statusCode': 200,
        'body': json.dumps('Done')
    }
