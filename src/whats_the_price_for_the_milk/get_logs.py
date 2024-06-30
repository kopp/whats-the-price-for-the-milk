"""
Extract price data from github action logs.
"""

import datetime
import io
import json
import os
import re
import zipfile
from pathlib import Path
from typing import List, NamedTuple, Optional

import pandas as pd
import requests
import typed_argparse as tap

TOKEN_ENV = "GITHUB_AUTH_TOKEN"
TOKEN_PATH = Path(__file__).parent.parent.parent / "github_token.json"

NEXT_PAGE_RE = re.compile(r'<(\S+)>; rel="next"')
PRICE_OUTPUT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z) (\d+\.\d{2})$")


class TimeAndPrice(NamedTuple):
    time: datetime.datetime
    price: float


_token: Optional[str] = None


def _get_token() -> str:
    global _token
    if _token is not None:
        return _token
    token = os.environ.get(TOKEN_ENV, None)
    if token is not None:
        _token = token
        return _token
    if TOKEN_PATH.exists():
        _token = json.loads(TOKEN_PATH.read_text())["token"]
        return _token
    raise ValueError(
        f"Please specify a github access token in environment variable '{TOKEN_ENV}' or file '{TOKEN_PATH.absolute()}'."
        "\nUse a token that has Actions:read access to the respository."
    )


def _get_next_page_url(link_headers: str) -> Optional[str]:
    for link in link_headers.split(","):
        if (match := NEXT_PAGE_RE.match(link)) is not None:
            return match.group(1)
    return None


def get_all_workflow_runs() -> List[int]:
    url = "https://api.github.com/repos/kopp/whats-the-price-for-the-milk/actions/runs?status=success&per_page=100"

    run_ids: List[int] = []

    while True:
        response = requests.get(
            url=url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {_get_token()}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        run_ids.extend([int(run["id"]) for run in response.json()["workflow_runs"]])

        next_url = _get_next_page_url(response.headers["link"])
        if next_url is None:
            return run_ids
        else:
            url = next_url


def _extract_time_and_price_from_logs(logs: str) -> TimeAndPrice:
    for line in logs.splitlines():
        if (match := PRICE_OUTPUT_RE.match(line)) is not None:
            return TimeAndPrice(
                time=datetime.datetime.fromisoformat(match.group(1)),
                price=float(match.group(2)),
            )
    raise ValueError("Unable to extract time from logs.")


def get_time_and_price_from_run(run_id: int) -> TimeAndPrice:

    url = f"https://api.github.com/repos/kopp/whats-the-price-for-the-milk/actions/runs/{run_id}/logs"

    response = requests.get(
        url=url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {_get_token()}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    assert response.ok, "Unable to fetch logs from github."

    logs = zipfile.ZipFile(io.BytesIO(response.content)).read("0_check-price.txt").decode()

    return _extract_time_and_price_from_logs(logs)


def get_times_and_prices_from_runs(run_ids: List[int]) -> pd.DataFrame:
    values = []
    for i, run_id in enumerate(run_ids):
        try:
            print(f"{i}/{len(run_ids)}: {run_id}...")
            values.append(get_time_and_price_from_run(run_id))
        except Exception as e:
            print(f"Skipping {run_id} due to {e}.")

    return pd.DataFrame(values)


def get_prices_as_table():
    all_runs = get_all_workflow_runs()
    df = get_times_and_prices_from_runs(all_runs)
    print(df.describe())
    output_file = "known_prices.csv"
    df.to_csv(output_file)
    print(f"Wrote raw data to {output_file}")


# CLI -------------------------------------------------------------------------


class _Arguments(tap.TypedArgs):
    pass


def _run(args: _Arguments):
    get_prices_as_table()


def main():
    tap.Parser(_Arguments, description=__doc__).bind(_run).run()


if __name__ == "__main__":
    main()
