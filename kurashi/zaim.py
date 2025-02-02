import csv
import json
from datetime import datetime
from typing import Optional

import click
import requests
from bs4 import BeautifulSoup, Tag


@click.command("zaim")
@click.argument("month", required=False)
@click.option("--username", envvar="ZAIM_USERNAME", help="ZAIM_USERNAME")
@click.option("--password", envvar="ZAIM_PASSWORD", help="ZAIM_PASSWORD")
def zaim(month: Optional[str], username: str, password: str) -> None:
    if not month:
        month = datetime.now().strftime("%Y%m")
    if not username or not password:
        exit(1)

    session = requests.Session()
    res = session.get("https://zaim.net/user_session/new")
    html = BeautifulSoup(res.text, "html.parser")
    token = html.find("input", {"name": "csrf_token"})
    if not isinstance(token, Tag):
        click.secho("Cannot get token", fg="red")
        exit(1)

    token_value = token["value"]
    data = {
        "csrf_token": token_value,
        "email": username,
        "password": password,
    }
    session.post("https://id.kufu.jp/signin/basic", data=data)
    session.get(f"https://zaim.net/money?month={month}")
    res = session.get(f"https://zaim.net/money/details?month={month}")
    data = json.loads(res.text)
    items = data.get("items", [])
    items = [x for x in items if x.get("calc_class", "") == "add_circle_outline"]
    result: list[list[str]] = []
    for x in items:
        parsed_date = x.get("parsed_date", "")
        mode = x.get("mode", "")
        amount = x.get("amount", "")
        place = x.get("place", "")
        from_account_name = x.get("from_account_name", "")
        to_account_name = x.get("to_account_name", "")
        account = from_account_name if from_account_name else to_account_name
        item = [parsed_date.replace("-", "/"), mode, place, amount, account]
        result.insert(0, item)
    with open(f"{month}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(result)
