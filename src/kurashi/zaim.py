import csv
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import click
import requests
from bs4 import BeautifulSoup


def _request(session: requests.Session, stage: str, method: str, url: str, **kwargs: Any) -> requests.Response:
    try:
        response = getattr(session, method)(url, timeout=30, **kwargs)
        response.raise_for_status()
        return response
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else "不明"
        raise click.ClickException(f"{stage}に失敗しました（HTTP {status}）。") from error
    except requests.Timeout as error:
        raise click.ClickException(f"{stage}がタイムアウトしました。") from error
    except requests.exceptions.SSLError as error:
        raise click.ClickException(f"{stage}で TLS 証明書を検証できませんでした。") from error
    except requests.ConnectionError as error:
        raise click.ClickException(f"{stage}で接続に失敗しました。ネットワークや DNS を確認してください。") from error
    except requests.RequestException as error:
        raise click.ClickException(f"{stage}で通信エラーが発生しました（{type(error).__name__}）。") from error


def _rows(items: list[dict[str, Any]]) -> list[list[Any]]:
    rows = []
    for item in items:
        if item.get("calc_class") != "add_circle_outline":
            continue
        rows.append(
            [
                str(item.get("parsed_date") or "").replace("-", "/"),
                item.get("mode") or "",
                item.get("place") or "",
                item.get("amount", ""),
                item.get("from_account_name") or item.get("to_account_name") or "",
            ]
        )
    return list(reversed(rows))


def _fetch_items(session: requests.Session, month: str, username: str, password: str) -> list[dict[str, Any]]:
    response = _request(session, "ログイン画面の取得", "get", "https://zaim.net/user_session/new")
    login_url = urlparse(response.url)
    if login_url.scheme != "https" or login_url.hostname != "id.kufu.jp":
        raise click.ClickException("ログイン画面の遷移先が想定と異なります。")
    token = BeautifulSoup(response.text, "html.parser").find("input", {"name": "csrf_token"})
    if not token or not token.get("value"):
        raise click.ClickException("ログイン用の CSRF トークンが見つかりません。ログイン画面の仕様が変わった可能性があります。")

    response = _request(
        session,
        "ログイン",
        "post",
        "https://id.kufu.jp/signin/basic",
        data={"csrf_token": token.get("value"), "email": username, "password": password},
        headers={"Origin": "https://id.kufu.jp", "Referer": response.url},
    )
    response = _request(session, "明細画面の取得", "get", "https://zaim.net/money", params={"month": month})
    host = urlparse(response.url).hostname or ""
    if host != "zaim.net" and not host.endswith(".zaim.net"):
        raise click.ClickException("Zaim にログインできませんでした。認証情報や追加認証の有無を確認してください。")
    if BeautifulSoup(response.text, "html.parser").select_one('input[type="password"]'):
        raise click.ClickException("Zaim にログインできませんでした。認証情報や追加認証の有無を確認してください。")

    response = _request(session, "明細データの取得", "get", "https://zaim.net/money/details", params={"month": month}, headers={"Accept": "application/json"})
    host = urlparse(response.url).hostname or ""
    if host != "zaim.net" and not host.endswith(".zaim.net"):
        raise click.ClickException("Zaim の認証が必要です。認証情報や追加認証の有無を確認してください。")
    try:
        data = response.json()
    except ValueError as error:
        raise click.ClickException("Zaim 明細を取得できませんでした。認証状態または応答形式を確認してください。") from error
    if not isinstance(data, dict) or not isinstance(data.get("items"), list) or not all(isinstance(item, dict) for item in data["items"]):
        raise click.ClickException("Zaim 明細の形式が不正です。CSV は保存していません。")
    return data["items"]


@click.command("zaim", help="Zaim の月別明細を CSV に保存する")
@click.argument("month", required=False)
@click.option("--username", envvar="ZAIM_USERNAME", required=True, help="Zaim のメールアドレス")
@click.option("--password", envvar="ZAIM_PASSWORD", required=True, help="Zaim のパスワード")
def zaim(month: str, username: str, password: str) -> None:
    month = month or datetime.now().strftime("%Y%m")
    if not re.fullmatch(r"\d{6}", month) or not 1 <= int(month[4:]) <= 12 or int(month[:4]) == 0:
        raise click.BadParameter("YYYYMM 形式の有効な月を指定してください。", param_hint="month")
    with requests.Session() as session:
        rows = _rows(_fetch_items(session, month, username, password))
    with open(f"{month}.csv", "w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerows(rows)
    click.echo(f"{month}.csv に {len(rows)} 件保存しました。")
