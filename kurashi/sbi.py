import click
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from kurashi.utils import post


@click.command('sbi', help='')
@click.option('--username', envvar='SBI_USERNAME')
@click.option('--password', envvar='SBI_PASSWORD')
@click.option('--api', envvar='SBI_API_URL')
@click.option('--no-post', is_flag=True)
def sbi(username, password, api, no_post):
    if not (username and password):
        click.echo('環境変数を設定してください')
        return

    sesstion = requests.Session()
    res = sesstion.get('https://www.sbisec.co.jp/ETGate')
    html = BeautifulSoup(res.text, 'html.parser')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-User': '?1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
    }
    data = {
        'JS_FLG': '0',
        'BW_FLG': '0',
        '_ControlID': 'WPLETlgR001Control',
        '_DataStoreID': 'DSWPLETlgR001Control',
        '_PageID': 'WPLETlgR001Rlgn20',
        '_ActionID': 'login',
        'getFlg': 'on',
        'allPrmFlg': 'on',
        '_ReturnPageInfo': 'WPLEThmR001Control/DefaultPID/DefaultAID/DSWPLEThmR001Control',
        'user_id': username,
        'user_password': password,
    }

    res = sesstion.post('https://www.sbisec.co.jp/ETGate/', data=data, headers=headers)
    html = BeautifulSoup(res.text, 'html.parser')
    action = html.find('form', {'name': 'formSwitch'})['action']
    ctoken = html.find('input', {'name': 'ctoken'})['value']
    login_date_time = html.find('input', {'name': 'LoginDateTime'})['value']
    tengun_id = html.find('input', {'name': '_TENGUN_ID'})['value']

    data = {
        'ctoken': ctoken,
        'LoginDateTime': login_date_time,
        '_TENGUN_ID': tengun_id,
        '_ActionID': 'login',
        '_PageID': 'WPLETlgR001Rlgn20',
        'BW_FLG': '0',
        'allPrmFlg': 'on',
        'JS_FLG': '0',
        '_DataStoreID': 'DSWPLETlgR001Control',
        '_ControlID': 'WPLETlgR001Control',
        'getFlg': 'on',
        '_ReturnPageInfo': 'WPLEThmR001Control/DefaultPID/DefaultAID/DSWPLEThmR001Control',
    }
    sesstion.post(action, verify=False, headers=headers, data=data)

    now = datetime.now().strftime('%Y/%m/%d')
    url = 'https://site2.sbisec.co.jp/ETGate/?_ControlID=WPLETpfR001Control&_PageID=DefaultPID&_DataStoreID=DSWPLETpfR001Control&_ActionID=DefaultAID&getFlg=on'
    res = sesstion.get(url, verify=False, headers=headers)
    res.encoding = res.apparent_encoding
    html = BeautifulSoup(res.text, 'html.parser')
    middleAria = html.find('div', class_='middleArea2')
    tables = []
    for item in middleAria.find_all('table'):
        if item.get('width') == '100%' and item.get('cellspacing') == '1' and item.get('cellpadding') == '4':
            tables.append(item.find_all('tr'))
    result = []
    for t in tables:
        for row in t[1:]:
            td = row.find_all('td')
            type = ''
            if '現買' in td[0].text:
                type = '株'
            elif '買付' in td[0].text:
                type = '投資信託'
            elif '積立' in td[0].text:
                type = 'NISA'
            name = td[1].find('a').text
            value = td[10].text.replace(',', '')
            result.append(f'{now},{name},{type},{value}')
    click.echo(result)
    if not no_post:
        post(api, result)
