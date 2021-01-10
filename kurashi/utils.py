import json
import requests


def post(url, data):
    headers = {'Content-Type': 'application/json'}
    requests.post(url, json.dumps(data), headers=headers)
