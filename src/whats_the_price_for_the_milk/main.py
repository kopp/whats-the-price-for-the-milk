"""
Get the current price for a certain commodity like milk or oil.
"""

from enum import StrEnum
from typing import Optional

import typed_argparse as tap

from .callmebot import ENV_CALLMEBOT_NUMBER, ENV_CALLMEBOT_TOKEN, send_callmebot_message
from .milk_price import MILK_URL, get_current_milk_price
from .oil_price import OIL_URL, get_current_oil_price
from .techulus import ENV_TUCHULUS_API_KEY, send_techulus_message

EXIT_OK = 0
EXIT_FAIL = 1


# push notification -----------------------------------------------------------


class _PushService(StrEnum):
    callmebot = "callmebot"
    techulus = "techulus"


_PUSH_VIA = {
    _PushService.callmebot: send_callmebot_message,
    _PushService.techulus: send_techulus_message,
}

# web scraping ----------------------------------------------------------------


class _Commodity(StrEnum):
    milk = "milk"
    oil = "oil"


_GET_CURRENT_PRICE_FOR = {
    _Commodity.milk: get_current_milk_price,
    _Commodity.oil: get_current_oil_price,
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
        help="Send a message if value is below this threshold.",
        default=None,
    )
    push_service: Optional[_PushService] = tap.arg(
        help=(
            "Use this push service."
            " Required if a message needs to get sent."
            f" SERVICE {_PushService.callmebot}:"
            " Uses callmebot.com and expects phone number under environment variable"
            f" {ENV_CALLMEBOT_NUMBER} and API key under {ENV_CALLMEBOT_TOKEN}."
            f" SERVICE {_PushService.techulus}:"
            " Uses the push.techulus.com API to push to the APP of a connected phone."
            f" Expects API key under {ENV_TUCHULUS_API_KEY}."
        ),
        default=None,
    )
    message_price: bool = tap.arg(
        help="Send a message with the current price regardless of its value.",
    )

    def assert_valid(self) -> None:
        """Raise ValueError if this is invalid."""
        might_send_message = self.message_if_below is not None or self.message_price
        if might_send_message and self.push_service is None:
            raise ValueError("Please specify a push service if messaging is requested.")


def _run(args: _Arguments) -> None:
    args.assert_valid()
    get_price = _GET_CURRENT_PRICE_FOR[args.commodity]
    price = get_price()
    print(price)

    execution_ok = True
    if args.message_price or (args.message_if_below is not None and price < args.message_if_below):
        if args.message_if_below is None:
            text = f"Current price for {args.commodity} is *{price:.2f} \N{euro sign}*."
        else:
            text = f"Current price *{price:.2f} \N{euro sign}* is below {args.message_if_below:.2f} \N{euro sign} for {args.commodity}."
        assert args.push_service is not None, "Need to specify a push service to send a message"
        send = _PUSH_VIA[args.push_service]
        is_sent = send(text)
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
