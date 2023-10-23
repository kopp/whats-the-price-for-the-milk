"""
Get the current price for a certain milk.
"""

import os
import sys
from urllib.parse import quote
from typing import NamedTuple, Optional
from bs4 import BeautifulSoup
import requests
import typed_argparse as tap


PRODUCT_URL = "https://nomi.shop/oatly-haferdrink-voll-6er-pack"
EXIT_OK = 0
EXIT_FAIL = 1

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php?phone={phone}&text={text}&apikey={key}"
ENV_CALLMEBOT_NUMBER = "CALLMEBOT_NUMBER"
ENV_CALLMEBOT_TOKEN = "CALLMEBOT_TOKEN"


# callmebot -------------------------------------------------------------------


class CallMeBotConnection(NamedTuple):
    number: str
    token: str


def _get_callmebot_data_from_env() -> CallMeBotConnection:
    error_message = ""
    if ENV_CALLMEBOT_NUMBER not in os.environ:
        error_message += f" Number expected in {ENV_CALLMEBOT_NUMBER}."
    if ENV_CALLMEBOT_TOKEN not in os.environ:
        error_message += f" Token expected in {ENV_CALLMEBOT_NUMBER}"
    if len(error_message) > 0:
        raise ValueError("Error retrieving callmebot data from environment:" + error_message)
    return CallMeBotConnection(
        number=os.environ[ENV_CALLMEBOT_NUMBER],
        token=os.environ[ENV_CALLMEBOT_TOKEN],
    )


def _get_callmebot_url(text: str) -> str:
    connection = _get_callmebot_data_from_env()
    return CALLMEBOT_URL.format(
        phone=connection.number,
        key=connection.token,
        text=quote(text),
    )


def _send_callmebot_message(text: str) -> bool:
    url = _get_callmebot_url(text)
    response = requests.get(url)
    if not response.ok:
        print(
            "Error sending callmebot message '{text}' to '{url}': '{response}' (text '{response.text}')",
            file=sys.stderr,
        )
    return response.ok


# web scraping ----------------------------------------------------------------


def _get_current_price() -> float:
    """Return the current price in Euros."""
    response = requests.get(PRODUCT_URL, timeout=10)
    assert response.status_code == 200, f"faulty response {response}"
    soup = BeautifulSoup(response.text, features="html.parser")
    prices = soup.find_all("p", {"class": "product-detail-price"})
    assert len(prices) > 0, "Unable to find price in page"
    text: str = prices[0].text
    price = float(text.strip().rstrip("\xa0€*").replace(",", "."))
    return price


# CLI -------------------------------------------------------------------------


class _Arguments(tap.TypedArgs):
    check_is_above: Optional[float] = tap.arg(
        help=f"Return {EXIT_OK} if price is above this threshold or {EXIT_FAIL} if below or equal."
        " Note, that the script may fail for other reasons even if the price is above.",
        default=None,
    )
    message_if_below: Optional[float] = tap.arg(
        help="Send a message if value is below this threshold."
        " Uses callmebot.com and expects phone number under environment variable"
        f" {ENV_CALLMEBOT_NUMBER} and API key under {ENV_CALLMEBOT_TOKEN}.",
        default=None,
    )


def _run(args: _Arguments) -> None:
    price = _get_current_price()
    print(price)

    execution_ok = True
    if args.message_if_below is not None and price < args.message_if_below:
        text = f"Current price *{price:.2f} \N{euro sign}* is below {args.message_if_below:.2f} \N{euro sign} at {PRODUCT_URL}."
        is_sent = _send_callmebot_message(text)
        execution_ok = is_sent and execution_ok
    if args.check_is_above is not None:
        is_above = price > args.check_is_above
        execution_ok = execution_ok and is_above

    return_code = EXIT_OK if execution_ok else EXIT_FAIL
    raise SystemExit(return_code)


def main():
    """Entry point of CLI script."""
    description = __doc__ + f" Checking website {PRODUCT_URL} for that."
    tap.Parser(_Arguments, description=description).bind(_run).run()
