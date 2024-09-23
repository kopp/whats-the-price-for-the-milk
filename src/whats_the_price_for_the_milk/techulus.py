"""Send push notifications via push by techulus."""

import os
import sys

import requests

# See https://docs.push.techulus.com/api-documentation-1

ENV_TUCHULUS_API_KEY = "PUSH_TUCHULUS_API_KEY"


def _get_techulus_api_key_from_env() -> str:
    error_message = ""
    if (api_key := os.environ.get(ENV_TUCHULUS_API_KEY)) is None:
        error_message += f" API key expected in {ENV_TUCHULUS_API_KEY}"
    if len(error_message) > 0:
        raise ValueError("Error retrieving techulus data from environment:" + error_message)
    assert api_key is not None, "No API key available from environment."
    return api_key


def send_techulus_message(text: str) -> bool:

    url = "https://push.techulus.com/api/v1/notify"

    response = requests.post(
        url,
        headers={
            "x-api-key": _get_techulus_api_key_from_env(),
            "Content-Type": "application/json",
        },
        json={
            "title": "New Price Info",
            "body": text,
            "channel": "prices",
            "sound": "correct",
        },
    )
    if response.status_code == 200:
        response_data = response.json()
        sending_worked = response_data["success"]
        print(f"Response for sending: {response_data}")
    else:
        sending_worked = False
    if not sending_worked:
        print(
            f"Error sending callmebot message '{text}' to '{url}': '{response}' (text '{response.text}')",
            file=sys.stderr,
        )
    return sending_worked
