"""
Get the current price for a certain milk.
"""

from typing import Optional
from bs4 import BeautifulSoup
import requests
import typed_argparse as tap


PRODUCT_URL = "https://nomi.shop/oatly-haferdrink-voll-6er-pack"
EXIT_OK = 0
EXIT_FAIL = 1


class _Arguments(tap.TypedArgs):
    is_above: Optional[float] = tap.arg(
        help=f"Return {EXIT_OK} if price is above this threshold or {EXIT_FAIL} if below or equal.",
        default=None,
    )


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


def _run(args: _Arguments) -> None:
    price = _get_current_price()
    print(price)
    if args.is_above is not None:
        return_code = EXIT_OK if price > args.is_above else EXIT_FAIL
        raise SystemExit(return_code)


def main():
    """Entry point of CLI script."""
    tap.Parser(_Arguments, description=__doc__).bind(_run).run()
