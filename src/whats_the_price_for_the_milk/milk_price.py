"""Obtain the current price for milk from the web."""

import requests
from bs4 import BeautifulSoup

MILK_URL = "https://nomi.shop/oatly-haferdrink-voll-6er-pack"


def get_current_milk_price() -> float:
    """Return the current price in Euros."""
    response = requests.get(MILK_URL, timeout=10)
    assert response.status_code == 200, f"faulty response {response}"
    soup = BeautifulSoup(response.text, features="html.parser")
    prices = soup.find_all("p", {"class": "product-detail-price"})
    assert len(prices) > 0, "Unable to find price in page"
    text: str = prices[0].text
    price = float(text.strip().rstrip("\xa0€*").replace(",", "."))
    return price
