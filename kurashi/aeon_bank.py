import re
import click
import requests
from datetime import datetime
from bs4 import BeautifulSoup

from kurashi.utils import post


def _arg_split(_, __, value):
    return [x for x in value.split(',')]


@click.command('aeonbank', help='イオン銀行から残高を取得する')
@click.option('--username', envvar='AEON_BANK_USERNAME', help='AEON_BANK_USERNAME')
@click.option('--password', envvar='AEON_BANK_PASSWORD', help='AEON_BANK_PASSWORD')
@click.option('--questions', envvar='AEON_BANK_QUESTIONS', help='AEON_BANK_QUESTIONS', callback=_arg_split)
@click.option('--answers', envvar='AEON_BANK_ANSWERS', help='AEON_BANK_ANSWERS', callback=_arg_split)
@click.option('--api-url', envvar='AEON_BANK_API_URL', help='AEON_BANK_API_URL')
@click.option('--no-post', is_flag=True, help='POSTしない')
def aeon_bank(username, password, questions, answers, api_url, no_post):
    if not (username and password and questions and answers):
        click.echo('環境変数を設定してください')
        return

    aikotoba = dict(zip(questions, answers))
    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' + \
        'Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75'
    headers = {
        'User-Agent': ua,
    }

    session = requests.Session()
    session.get('https://www.aeonbank.co.jp/login/ib_02.html', headers=headers)
    session.get('https://ib.aeonbank.co.jp/0040/B/B/B/C100/KBC11BN000B000.do', headers=headers)
    param = {
        'cntrId': username,
        'scndPinNmbr': password,
        'kba_css_path': 'https://ib.aeonbank.co.jp/0040/B/image/1',
        'scrnId': 'KBC11BN000B',
    }
    res = session.post('https://ib.aeonbank.co.jp/0040/B/B/B/C100/KBC11BN004B001.do', data=param, headers=headers)
    html = BeautifulSoup(res.text, 'html.parser')
    uuid = html.find('input', {'name': 'uuid'})['value']

    answer = ''
    for question in aikotoba.keys():
        if re.search(question, res.text):
            answer = aikotoba[question]
    if not answer:
        click.echo('question and answer is not valid')
        return

    aikotoba_param = {
        'wcwdAskRspo': answer,
        'regiClas': 0,
        'uuid': uuid,
        'kba_css_path': 'https://ib.aeonbank.co.jp/0040/B/image/1',
        'scrnId': 'KBC11BN010B',
    }
    res = session.post('https://ib.aeonbank.co.jp/0040/B/B/B/C100/KBC11BN010B001.do', data=aikotoba_param, headers=headers)
    html = BeautifulSoup(res.text, 'html.parser')
    tmp = html.find('div', id='balnAmount2')
    amount = tmp.text
    click.echo(amount)
    if not no_post:
        value = amount.replace(',', '').replace('円', '')
        now = datetime.now()
        post(api_url, {'date': now.strftime("%Y/%m"), 'value': int(value)})
