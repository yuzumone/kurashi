import unittest
from unittest.mock import Mock, patch

import click
import requests
from click.testing import CliRunner

from kurashi.zaim import _fetch_items, _request, _rows, zaim


def response(url, text="", data=None):
    result = Mock(url=url, text=text)
    result.json.return_value = data
    return result


class ZaimTests(unittest.TestCase):
    def test_http_error_reports_stage_and_status_without_url(self):
        session = Mock()
        result = response("https://id.kufu.jp/?token=secret")
        result.status_code = 403
        result.raise_for_status.side_effect = requests.HTTPError(response=result)
        session.post.return_value = result
        with self.assertRaises(click.ClickException) as raised:
            _request(session, "ログイン", "post", "https://id.kufu.jp/signin/basic")
        self.assertIn("ログイン", str(raised.exception))
        self.assertIn("403", str(raised.exception))
        self.assertNotIn("secret", str(raised.exception))

    def test_rows_preserve_legacy_order_and_filter(self):
        items = [
            {"calc_class": "add_circle_outline", "parsed_date": "2026-11-02", "mode": "payment", "place": "店", "amount": 100, "from_account_name": "財布"},
            {"calc_class": "other", "amount": 200},
            {"calc_class": "add_circle_outline", "parsed_date": "2026-11-01", "amount": 0, "to_account_name": "銀行"},
        ]
        self.assertEqual(_rows(items), [["2026/11/01", "", "", 0, "銀行"], ["2026/11/02", "payment", "店", 100, "財布"]])

    def test_fetch_uses_csrf_and_session(self):
        session = Mock()
        items = [{"amount": 100}]
        session.get.side_effect = [response("https://id.kufu.jp/", '<input name="csrf_token" value="abc">'), response("https://zaim.net/money"), response("https://zaim.net/money/details", data={"items": items})]
        session.post.return_value = response("https://zaim.net/")
        self.assertEqual(_fetch_items(session, "202611", "user", "pass"), items)
        self.assertEqual(session.post.call_args.kwargs["data"], {"csrf_token": "abc", "email": "user", "password": "pass"})
        self.assertEqual(session.post.call_args.kwargs["headers"], {"Origin": "https://id.kufu.jp", "Referer": "https://id.kufu.jp/"})

    def test_login_redirect_rejected(self):
        session = Mock()
        session.get.side_effect = [response("https://id.kufu.jp/", '<input name="csrf_token" value="abc">'), response("https://id.kufu.jp/signin")]
        with self.assertRaises(click.ClickException):
            _fetch_items(session, "202611", "user", "pass")

    def test_invalid_response_does_not_overwrite_csv(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("202611.csv", "w") as file:
                file.write("existing")
            with patch("kurashi.zaim._fetch_items", side_effect=click.ClickException("invalid")):
                result = runner.invoke(zaim, ["202611", "--username", "user", "--password", "pass"])
            self.assertNotEqual(result.exit_code, 0)
            with open("202611.csv") as file:
                self.assertEqual(file.read(), "existing")

    def test_invalid_month_rejected(self):
        result = CliRunner().invoke(zaim, ["202613", "--username", "user", "--password", "pass"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("YYYYMM", result.output)


if __name__ == "__main__":
    unittest.main()
