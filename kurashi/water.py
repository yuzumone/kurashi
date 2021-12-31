import re
import click
import requests
import mojimoji
from bs4 import BeautifulSoup

from kurashi.utils import post


@click.command('water', help='東京都水道局から利用料金を取得する')
@click.option('--username', envvar='WATER_USERNAME', help='WATER_USERNAME')
@click.option('--password', envvar='WATER_PASSWORD', help='WATER_PASSWORD')
@click.option('--water-api-url', envvar='WATER_API_URL', help='WATER_API_URL')
@click.option('--no-post', is_flag=True, help='POSTしない')
def water(username, password, water_api_url, no_post):
    if not (username and password):
        click.echo('環境変数を設定してください')
        return

    session = requests.Session()
    first = session.get('https://suidonet.waterworks.metro.tokyo.lg.jp/inet-service/members/login')
    first.encoding = first.apparent_encoding
    html = BeautifulSoup(first.text, 'html.parser')
    token = html.find('input', {'name': 'wap_PageToken'})['value']
    param = {
        'userName': username,
        'password': password,
        'wap_PageToken': token,
    }

    session.post('https://suidonet.waterworks.metro.tokyo.lg.jp/inet-service/members/login', data=param)
    notice = session.get('https://suidonet.waterworks.metro.tokyo.lg.jp/inet-service/members/member_page/notice_of_consumption')
    html = BeautifulSoup(notice.text, 'html.parser')
    selected = html.find('option', selected=True).text
    date = selected.split('-')[1].replace('年', '/').replace('月分', '')
    result = html.findAll('font', {'size': 4})
    for x in [x.text for x in result]:
        tmp = mojimoji.zen_to_han(x)
        match = re.match(r'\d+', tmp.replace(',', ''))
        if match:
            price = match.group()
            click.echo(f'water: {date} {price}')
            if not no_post:
                post(water_api_url, {'date': date, 'value': int(price)})
