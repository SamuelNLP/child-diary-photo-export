"""Export media files from ChildDiary using authenticated API requests."""

import argparse
import concurrent.futures
import os
import shutil
import tarfile
import time
import urllib.request
import uuid
import zipfile
from datetime import datetime
from functools import partial
from pathlib import Path
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


def parse_media_date(date_str: str) -> datetime.date:
    """Parse date string handling both with and without microseconds.

    Parameters
    ----------
    date_str : str
        Date string from API, e.g. '2025-12-15T17:32:45Z' or '2025-12-15T17:32:45.123456Z'.

    Returns
    -------
    datetime.date
        Parsed date.
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # With microseconds
        "%Y-%m-%dT%H:%M:%SZ",  # Without microseconds
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")


def get_image(
    media_item: dict[str, Any], page_number: int, output_dir: str
) -> str | None:
    """Download a media item and return the file path on success.

    Parameters
    ----------
    media_item : dict of str to Any
        Item payload returned by ``/api/media``.
    page_number : int
        Source page number where this item was listed.
    output_dir : str
        Directory to save the downloaded file.

    Returns
    -------
    str | None
        Path to the downloaded file on success, None on failure.
    """
    created_date = parse_media_date(media_item["CreatedOn"])
    file_extension = media_item["Extension"]
    file_name = f"{created_date}_{str(uuid.uuid4())[:6]}{file_extension}"
    destination = str(Path(output_dir) / file_name)

    try:
        download_image(media_item["Url"], destination)
        print(f"page_number={page_number}, file_name={file_name}")
        return destination
    except Exception as download_error:  # noqa: BLE001
        print(
            f"Failed to download image for page_number={page_number}: {media_item['Url']}"
        )
        print(download_error)
        return None


def check_disk_usage(directory: str, threshold: float = 90.0) -> bool:
    """Check disk usage and prompt if above threshold.

    Parameters
    ----------
    directory : str
        Directory to check disk usage for.
    threshold : float
        Percentage threshold (default: 90.0).

    Returns
    -------
    bool
        True to continue, False to stop.
    """
    usage = shutil.disk_usage(directory)
    percent_used = (usage.used / usage.total) * 100

    if percent_used >= threshold:
        print(f"WARNING: Disk usage at {percent_used:.1f}% (>= {threshold}%)")
        response = input("Disk space running low. Continue? [y/N]: ").strip().lower()
        return response in ("y", "yes")
    return True


def compress_files(
    file_list: list[str], archive_name: str, compress_type: str = "zip"
) -> None:
    """Compress files into an archive and remove originals.

    Parameters
    ----------
    file_list : list[str]
        List of file paths to compress.
    archive_name : str
        Name for the compressed archive.
    compress_type : str, optional
        Compression type: zip (default), gzip, or bz2.
    """
    if not file_list:
        return

    output_dir = Path(file_list[0]).parent

    if compress_type == "zip":
        archive_path = output_dir / f"{archive_name}.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in file_list:
                zf.write(f, arcname=Path(f).name)
    elif compress_type == "gzip":
        archive_path = output_dir / f"{archive_name}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tf:
            for f in file_list:
                tf.add(f, arcname=Path(f).name)
    elif compress_type == "bz2":
        archive_path = output_dir / f"{archive_name}.tar.bz2"
        with tarfile.open(archive_path, "w:bz2") as tf:
            for f in file_list:
                tf.add(f, arcname=Path(f).name)
    else:
        print(f"Unknown/unsupported compression format {compress_type!r}. Skipping")
        return

    # Remove original files
    for f in file_list:
        os.remove(f)
        print(f"Compressed {Path(f).name} into {archive_path.name}")


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
    parser = argparse.ArgumentParser(
        description="Export media from ChildDiary to local files."
    )
    parser.add_argument(
        "-c",
        "--compress",
        choices=["zip", "gzip", "bz2"],
        metavar="TYPE",
        help="Compress each page's files after download (zip, gzip, bz2)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="media",
        metavar="DIR",
        help="Output directory for media files (default: media)",
    )
    parser.add_argument(
        "-p",
        "--start-page",
        type=int,
        default=1,
        metavar="N",
        help="Start downloading from page N (default: 1)",
    )
    args = parser.parse_args()

    if args.start_page < 1:
        parser.error("--start-page must be >= 1")

    os.makedirs(args.output_dir, exist_ok=True)
    session = create_authenticated_session()
    current_page = args.start_page

    while True:
        if not check_disk_usage(args.output_dir):
            print("Stopped due to low disk space.")
            break

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
            results = list(
                executor.map(
                    partial(
                        get_image, page_number=current_page, output_dir=args.output_dir
                    ),
                    page_media_items,
                )
            )

        downloaded_files = [r for r in results if r is not None]

        if args.compress:
            compress_files(downloaded_files, f"page_{current_page}", args.compress)

        page_elapsed_seconds = time.time() - page_start_time
        print(f"Page {current_page} took {page_elapsed_seconds} seconds")

        current_page += 1


if __name__ == "__main__":
    main()
