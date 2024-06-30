"""
Get the current price for a certain commodity like milk or oil.
"""

import json
import os
import sys
from enum import Enum
from typing import NamedTuple, Optional
from urllib.parse import quote

import requests
import typed_argparse as tap
from bs4 import BeautifulSoup

MILK_URL = "https://nomi.shop/oatly-haferdrink-voll-6er-pack"
OIL_URL = "https://www.heizoel24.de/api/kalkulation/berechnen"

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
        error_message += f" Token expected in {ENV_CALLMEBOT_TOKEN}"
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


def _check_response_ok(response: requests.Response) -> bool:
    if not response.ok:
        return False
    if "technical issues" in response.text:
        return False
    return True


def _send_callmebot_message(text: str) -> bool:
    url = _get_callmebot_url(text)
    response = requests.get(url)
    sending_worked = _check_response_ok(response)
    if not sending_worked:
        print(
            f"Error sending callmebot message '{text}' to '{url}': '{response}' (text '{response.text}')",
            file=sys.stderr,
        )
    return sending_worked


# web scraping ----------------------------------------------------------------


def _get_current_milk_price() -> float:
    """Return the current price in Euros."""
    response = requests.get(MILK_URL, timeout=10)
    assert response.status_code == 200, f"faulty response {response}"
    soup = BeautifulSoup(response.text, features="html.parser")
    prices = soup.find_all("p", {"class": "product-detail-price"})
    assert len(prices) > 0, "Unable to find price in page"
    text: str = prices[0].text
    price = float(text.strip().rstrip("\xa0€*").replace(",", "."))
    return price


def _get_current_oil_price() -> float:
    _OIL_API_HEADER = json.loads(
        """
        {
        "ZipCode": "71717",
        "Amount": 3000,
        "Stations": 1,
        "Product": {
            "Id": 1,
            "ClimateNeutral": false
        },
        "Parameters": [
            {
            "Key": "MaxDelivery",
            "Id": 5,
            "Modifier": -1,
            "Name": "maximal",
            "ShortName": null,
            "DisplayName": "max. Lieferfrist",
            "CalculatorName": "siehe Angebot",
            "SubText": null,
            "InfoText": null,
            "OrderText": null,
            "IconKey": null,
            "HasSpecialView": false,
            "IsUpselling": false,
            "BlackList": [],
            "Selected": true,
            "HasSubItems": false,
            "UseIcon": false
            },
            {
            "Key": null,
            "Id": 24,
            "Modifier": -1,
            "Name": "ganztägig möglich (7-18 Uhr)",
            "ShortName": null,
            "DisplayName": null,
            "CalculatorName": null,
            "SubText": null,
            "InfoText": null,
            "OrderText": null,
            "IconKey": null,
            "HasSpecialView": false,
            "IsUpselling": false,
            "BlackList": [],
            "Selected": true,
            "HasSubItems": false,
            "UseIcon": false
            },
            {
            "Key": null,
            "Id": -2,
            "Modifier": -1,
            "Name": "alle",
            "ShortName": "alle",
            "DisplayName": "alle",
            "CalculatorName": "alle",
            "SubText": null,
            "InfoText": null,
            "OrderText": null,
            "IconKey": null,
            "HasSpecialView": false,
            "IsUpselling": false,
            "BlackList": [],
            "Selected": true,
            "HasSubItems": false,
            "UseIcon": false
            },
            {
            "Key": null,
            "Id": 11,
            "Modifier": -1,
            "Name": "mit Hänger",
            "ShortName": "groß",
            "DisplayName": "TKW mit Hänger",
            "CalculatorName": "mit Hänger",
            "SubText": null,
            "InfoText": null,
            "OrderText": null,
            "IconKey": null,
            "HasSpecialView": false,
            "IsUpselling": false,
            "BlackList": [],
            "Selected": true,
            "HasSubItems": false,
            "UseIcon": true
            },
            {
            "Key": null,
            "Id": 9,
            "Modifier": -1,
            "Name": "bis 40m",
            "ShortName": "40m",
            "DisplayName": null,
            "CalculatorName": null,
            "SubText": null,
            "InfoText": null,
            "OrderText": null,
            "IconKey": null,
            "HasSpecialView": false,
            "IsUpselling": false,
            "BlackList": [],
            "Selected": true,
            "HasSubItems": false,
            "UseIcon": false
            }
        ],
        "CountryId": 1,
        "Cn": false,
        "Ap": false,
        "ProductGroupId": 1,
        "AppointmentPlus": false,
        "Ordering": 0,
        "UpsellCount": 0
        }
        """
    )
    response = requests.post(OIL_URL, timeout=10, json=_OIL_API_HEADER)
    assert response.status_code == 200, f"faulty response {response}"
    prices = response.json()
    lowest_price = min([p["UnitPrice"] for p in prices["Items"]])
    return lowest_price


class _Commodity(str, Enum):
    milk = "milk"
    oil = "oil"

    def __str__(self) -> str:
        return self.value


_GET_CURRENT_PRICE_FOR = {
    _Commodity.milk: _get_current_milk_price,
    _Commodity.oil: _get_current_oil_price,
}


# CLI -------------------------------------------------------------------------


class _Arguments(tap.TypedArgs):
    commodity: _Commodity = tap.arg(
        help="The commodity to check the price for.",
    )
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
    get_price = _GET_CURRENT_PRICE_FOR[args.commodity]
    price = get_price()
    print(price)

    execution_ok = True
    if args.message_if_below is not None and price < args.message_if_below:
        text = f"Current price *{price:.2f} \N{euro sign}* is below {args.message_if_below:.2f} \N{euro sign} for {args.commodity}."
        is_sent = _send_callmebot_message(text)
        execution_ok = is_sent and execution_ok
    if args.check_is_above is not None:
        is_above = price > args.check_is_above
        execution_ok = execution_ok and is_above

    return_code = EXIT_OK if execution_ok else EXIT_FAIL
    raise SystemExit(return_code)


def main():
    """Entry point of CLI script."""
    description = __doc__ + f" Checking website {MILK_URL} or {OIL_URL} for that."
    tap.Parser(_Arguments, description=description).bind(_run).run()
