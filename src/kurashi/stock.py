import json
import re
from datetime import datetime
from typing import Any, Optional

import click
import requests
from bs4 import BeautifulSoup

pattern = re.compile(r"window\.__PRELOADED_STATE__\s*=\s*({.*})", re.DOTALL)


@click.command("stock", help="")
@click.option("--db", envvar="DB")
@click.option("--token", envvar="TOKEN")
@click.option("--base", envvar="BASE_ID")
@click.option("--asset", envvar="ASSET_ID")
@click.option("--quotes", envvar="QUOTES_ID")
def stock(db: str, token: str, base: str, asset: str, quotes: str) -> None:
    session = requests.Session()
    assets = _get_assets(session, db, token, base, asset)
    if not assets:
        click.secho("error: cannot retrieve assets", fg="red")
        return

    now = datetime.now().strftime("%Y-%m-%d")
    for record in assets.get("records", []):
        asset_id = record["id"]
        price = _get_finance(session, f"{record['fields']['ticker_code']}")
        if not price:
            continue
        _post_db(session, db, token, base, quotes, now, price, asset_id)


def _get_assets(session: requests.Session, db: str, token: str, base: str, table: str) -> Optional[dict[str, Any]]:
    url = f"https://{db}/api/v3/data/{base}/{table}/records"
    headers = {"xc-token": token}
    try:
        res = session.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except requests.RequestException:
        return None

    try:
        data = json.loads(res.text)
        return data
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


def _post_db(session: requests.Session, db: str, token: str, base: str, table: str, date: str, price: str, asset_id: str) -> Optional[dict[str, Any]]:
    url = f"https://{db}/api/v3/data/{base}/{table}/records"
    headers = {"xc-token": token, "accept": "application/json", "Content-Type": "application/json"}
    payload = {"fields": {"quote_date": date, "close_price": price, "asset_id": {"id": str(asset_id)}}}
    try:
        res = session.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()
    except requests.RequestException:
        return None


def _get_finance(session: requests.Session, code: str) -> Optional[str]:
    url = "https://fin" + "ance.ya" + f"hoo.co.jp/quote/{code}"
    try:
        res = session.get(url, timeout=10)
        res.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    script = soup.find("script", string=re.compile(r"window\.__PRELOADED_STATE__\s*="))
    if not script:
        return None

    m = pattern.search(script.string)
    if not m:
        return None

    try:
        data = json.loads(m.group(1))
        price_str = data.get("mainStocksPriceBoard", {}).get("priceBoard", {}).get("price") or data.get("mainFundPriceBoard", {}).get("fundPrices", {}).get(
            "price"
        )
        if price_str:
            return price_str.replace(",", "")

    except (json.JSONDecodeError, ValueError, KeyError):
        return None

    return None
