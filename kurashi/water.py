import json
import click
import requests

from kurashi.utils import post


@click.command('water', help='東京都水道局から利用料金を取得する')
@click.option('--username', envvar='WATER_USERNAME', help='WATER_USERNAME')
@click.option('--email', envvar='WATER_EMAIL', help='WATER_EMAIL')
@click.option('--password', envvar='WATER_PASSWORD', help='WATER_PASSWORD')
@click.option('--water-api-url', envvar='WATER_API_URL', help='WATER_API_URL')
@click.option('--no-post', is_flag=True, help='POSTしない')
def water(username, email, password, water_api_url, no_post):
    if not (username and email and password):
        click.echo('環境変数を設定してください')
        return

    session = requests.Session()
    session.get('https://api.suidoapp.waterworks.metro.tokyo.lg.jp')
    param = {
        'loginId': email,
        'password': password,
    }
    res = session.post('https://api.suidoapp.waterworks.metro.tokyo.lg.jp/user/auth/login', data=json.dumps(param))
    data = json.loads(res.text)
    header = {
        'authorization': data['token'],
    }
    result = session.get(f'https://api.suidoapp.waterworks.metro.tokyo.lg.jp/user/meterdata/{username}', headers=header)
    d = json.loads(result.text)
    year = d['data']['seiDateEnd1'][:4]
    month = d['data']['seiDateEnd1'][4:]
    value = d['data']['toChAm']
    if not no_post:
        post(water_api_url, {'date': f'{year}/{month}', 'value': int(value)})
