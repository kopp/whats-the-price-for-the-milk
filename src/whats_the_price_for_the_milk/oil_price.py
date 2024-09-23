"""Get current price for oil from the web."""

import json

import requests

OIL_URL = "https://www.heizoel24.de/api/kalkulation/berechnen"


def get_current_oil_price() -> float:
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
