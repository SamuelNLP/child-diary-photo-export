import json
import uuid

import requests
from datetime import datetime
import urllib.request
from functools import partial
import concurrent.futures


def get_image(element, page):
    date = datetime.strptime(element["CreatedOn"], "%Y-%m-%dT%H:%M:%S.%fZ").date()
    extension = element["Extension"]

    try:
        urllib.request.urlretrieve(
            element["Url"], f"media/{date}_{str(uuid.uuid4())[:6]}{extension}"
        )
        print(f"{page=}, {str(date)=}")

    except:  # noqa
        print(element["Url"])


if __name__ == "__main__":
    with open("data/headers.json") as headers_json:
        headers = json.load(headers_json)

    page = 0

    while True:
        response = requests.get(
            "https://app.childdiary.net/api/media",
            params={"page": str(page)},
            headers=headers,
        )

        if response.status_code != 200 or response.text == "[]":
            break

        response_json = response.json()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(partial(get_image, page=page), response_json)

        page += 1
