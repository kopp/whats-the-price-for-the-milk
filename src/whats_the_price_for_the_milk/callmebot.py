"""
Use callmebot.com to send push notifications via WhatsApp.
"""

import os
import sys
from typing import NamedTuple
from urllib.parse import quote

import requests

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php?phone={phone}&text={text}&apikey={key}"
ENV_CALLMEBOT_NUMBER = "CALLMEBOT_NUMBER"
ENV_CALLMEBOT_TOKEN = "CALLMEBOT_TOKEN"


class _CallMeBotConnection(NamedTuple):
    number: str
    token: str


def _get_callmebot_data_from_env() -> _CallMeBotConnection:
    error_message = ""
    if ENV_CALLMEBOT_NUMBER not in os.environ:
        error_message += f" Number expected in {ENV_CALLMEBOT_NUMBER}."
    if ENV_CALLMEBOT_TOKEN not in os.environ:
        error_message += f" Token expected in {ENV_CALLMEBOT_TOKEN}"
    if len(error_message) > 0:
        raise ValueError("Error retrieving callmebot data from environment:" + error_message)
    return _CallMeBotConnection(
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


def send_callmebot_message(text: str) -> bool:
    url = _get_callmebot_url(text)
    response = requests.get(url)
    sending_worked = _check_response_ok(response)
    if not sending_worked:
        print(
            f"Error sending callmebot message '{text}' to '{url}': '{response}' (text '{response.text}')",
            file=sys.stderr,
        )
    return sending_worked
