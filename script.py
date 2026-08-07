"""Export media files from ChildDiary using authenticated API requests."""

import concurrent.futures
import os
import time
import urllib.request
import uuid
from datetime import datetime
from functools import partial
from typing import Any

import requests
from auth import get_credentials
from tenacity import retry
from tenacity import stop_after_attempt
from tenacity import wait_exponential


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
    reraise=True,
)
def download_image(image_url: str, destination: str) -> None:
    """Download one image to disk with retry behavior handled by tenacity.

    Parameters
    ----------
    image_url : str
        Public URL that points to the file.
    destination : str
        Local file path where the image will be written.

    Returns
    -------
    None
    """
    urllib.request.urlretrieve(image_url, destination)


def get_image(media_item: dict[str, Any], page_number: int) -> None:
    """Download a media item and log success/failure information.

    Parameters
    ----------
    media_item : dict of str to Any
        Item payload returned by ``/api/media``.
    page_number : int
        Source page number where this item was listed.

    Returns
    -------
    None
    """
    created_date = datetime.strptime(
        media_item["CreatedOn"], "%Y-%m-%dT%H:%M:%S.%fZ"
    ).date()
    file_extension = media_item["Extension"]
    file_name = f"{created_date}_{str(uuid.uuid4())[:6]}{file_extension}"

    try:
        download_image(media_item["Url"], f"media/{file_name}")
        print(f"page_number={page_number}, file_name={file_name}")
    except Exception as download_error:  # noqa: BLE001
        print(
            f"Failed to download image for page_number={page_number}: {media_item['Url']}"
        )
        print(download_error)


def create_authenticated_session() -> requests.Session:
    """Create an authenticated ChildDiary session using credentials from env vars or keyring.

    Returns
    -------
    requests.Session
        Authenticated HTTP session with login cookies set.
    """
    username, password = get_credentials()

    session = requests.Session()
    session.headers.update(
        {
            "accept": "application/json, text/plain, */*",
            "referer": "https://app.childdiary.net/main",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
        }
    )

    login_response = session.post(
        "https://app.childdiary.net/api/Account/login",
        json={
            "Username": username,
            "Password": password,
            "RememberMe": True,
        },
        timeout=30,
    )

    if login_response.status_code != 200:
        raise RuntimeError(
            f"Login failed ({login_response.status_code}): {login_response.text}"
        )

    return session


def main() -> None:
    """Fetch paginated media metadata and download each image in parallel.

    Returns
    -------
    None
    """
    os.makedirs("media", exist_ok=True)

    session = create_authenticated_session()

    current_page = 1

    while True:
        page_start_time = time.time()

        media_response = session.get(
            "https://app.childdiary.net/api/media",
            params={"page": str(current_page)},
            timeout=30,
        )

        if media_response.status_code != 200 or media_response.text == "[]":
            break

        page_media_items = media_response.json()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(partial(get_image, page_number=current_page), page_media_items)

        page_elapsed_seconds = time.time() - page_start_time
        print(f"Page {current_page} took {page_elapsed_seconds} seconds")

        current_page += 1


if __name__ == "__main__":
    main()
