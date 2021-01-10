import click
import requests
from bs4 import BeautifulSoup

from kurashi.utils import post


@click.command('tepco', help='くらしTEPCOから利用料金を取得する')
@click.option('--username', envvar='TEPCO_USERNAME', help='TEPCO_USERNAME')
@click.option('--password', envvar='TEPCO_PASSWORD', help='TEPCO_PASSWORD')
@click.option('--electric-id', envvar='TEPCO_ELECTRIC_ID', help='TEPCO_ELECTRIC_ID')
@click.option('--gas-id', envvar='TEPCO_GAS_ID', help='TEPCO_GAS_ID')
@click.option('--electric-api-url', envvar='ELECTRIC_API_URL', help='ELECTRIC_API_URL')
@click.option('--gas-api-url', envvar='GAS_API_URL', help='GAS_API_URL')
@click.option('--no-post', is_flag=True, help='POSTしない')
def tepco(username, password, electric_id, gas_id, electric_api_url, gas_api_url, no_post):
    if not (username and password and electric_id and gas_id):
        click.echo('環境変数を設定してください')
        return

    session = requests.Session()
    param = {
        'ACCOUNTUID': username,
        'PASSWORD': password,
        'HIDEURL': '/pf/ja/pc/mypage/home/index.page?',
        'LOGIN': 'EUAS_LOGIN',
    }
    session.post('https://www.kurashi.tepco.co.jp/kpf-login', data=param)

    electric_url = f'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/home/index.page?headerContractIndex={electric_id}'
    res = session.get(electric_url)
    html = BeautifulSoup(res.text, 'html.parser')
    text_date = html.find('p', class_='p-mypage-text__date').text
    date = text_date.replace('年', '/').replace('月分', '')
    text_price = html.find('p', class_='p-mypage-text__price').text
    price = text_price.replace(',', '').replace('円', '')
    click.echo(f'electric: {date} {price}')
    if not no_post:
        post(electric_api_url, {'date': date, 'value': int(price)})

    gas_url = f'https://www.kurashi.tepco.co.jp/pf/ja/pc/mypage/home/index.page?headerContractIndex={gas_id}'
    res = session.get(gas_url)
    html = BeautifulSoup(res.text, 'html.parser')
    text_date = html.find('p', class_='p-mypage-text__date').text
    date = text_date.replace('年', '/').replace('月分', '')
    text_price = html.find('p', class_='p-mypage-text__price').text
    price = text_price.replace(',', '').replace('円', '')
    click.echo(f'gas: {date} {price}')
    if not no_post:
        post(gas_api_url, {'date': date, 'value': int(price)})
