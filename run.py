import json

import requests
from datetime import datetime
import urllib.request


with open("data/cookies.json") as cookies_json:
    cookies = json.load(cookies_json)

with open("data/headers.json") as headers_json:
    headers = json.load(headers_json)

counter = 0
page = 0

while page < 5:
    response = requests.get(
        "https://app.childdiary.net/api/media",
        params={"page": str(page)},
        cookies=cookies,
        headers=headers,
    )

    if response.status_code != 200 or response.text == "[]":
        break

    a = response.json()

    for media in response.json():
        date = datetime.strptime(media["CreatedOn"], "%Y-%m-%dT%H:%M:%S.%fZ").date()

        if media["Type"] == "image/jpeg":
            image_data = requests.get(media["Url"]).content
            with open(f"photos/{counter}_{date}.jpg", "wb") as image_handler:
                image_handler.write(image_data)
        elif media["Type"] == "video/mp4":
            urllib.request.urlretrieve(media["Url"], f"videos/{counter}_{date}.mp4")
        else:
            print(media["Type"])

        counter += 1
        print(f"{page=}, {counter=}, {str(date)=}")

    page += 1
