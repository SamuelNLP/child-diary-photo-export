"""Tests for the CLI module with mocked API connections."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import responses

from childdiary_export.cli import (
    check_disk_usage,
    compress_files,
    create_authenticated_session,
    download_image,
    export,
    get_image,
    parse_media_date,
)

# =============================================================================
# Date parsing tests
# =============================================================================


def test_parse_date_without_microseconds():
    """Test parsing date string without microseconds."""
    result = parse_media_date("2025-12-15T17:32:45Z")
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 15


def test_parse_date_with_microseconds():
    """Test parsing date string with microseconds."""
    result = parse_media_date("2025-12-15T17:32:45.123456Z")
    assert result.year == 2025
    assert result.month == 12
    assert result.day == 15


def test_parse_date_invalid_format():
    """Test that invalid date format raises ValueError."""
    with pytest.raises(ValueError):
        parse_media_date("invalid-date")


# =============================================================================
# Image download tests
# =============================================================================


@patch("childdiary_export.cli.urllib.request.urlretrieve")
def test_download_image_success(mock_urlretrieve, temp_output_dir):
    """Test successful image download with mocked urllib."""
    image_url = "https://example.com/image.jpg"
    image_data = b"fake image data"
    output_path = temp_output_dir / "test_image.jpg"

    def mock_retrieve(url, dest):
        with open(dest, "wb") as f:
            f.write(image_data)

    mock_urlretrieve.side_effect = mock_retrieve

    download_image(image_url, str(output_path))

    assert output_path.exists()
    assert output_path.read_bytes() == image_data


# =============================================================================
# Media item processing tests
# =============================================================================


@patch("childdiary_export.cli.urllib.request.urlretrieve")
def test_get_image_with_valid_url(mock_urlretrieve, temp_output_dir):
    """Test downloading a media item with valid URL."""
    media_url = "https://example.com/media/123.jpg"

    def mock_retrieve(url, dest):
        with open(dest, "wb") as f:
            f.write(b"test media data")

    mock_urlretrieve.side_effect = mock_retrieve

    media_item = {
        "CreatedOn": "2025-01-01T10:00:00Z",
        "Extension": ".jpg",
        "Url": media_url,
    }

    result = get_image(media_item, 1, str(temp_output_dir))

    assert result is not None
    assert Path(result).exists()


def test_get_image_with_invalid_url(temp_output_dir):
    """Test handling of invalid media URL."""
    media_item = {
        "CreatedOn": "2025-01-01T10:00:00Z",
        "Extension": ".jpg",
        "Url": None,
    }

    result = get_image(media_item, 1, str(temp_output_dir))
    assert result is None


def test_get_image_with_missing_fields(temp_output_dir):
    """Test handling of missing required fields."""
    media_item = {
        "Url": "https://example.com/test.jpg",
    }

    with pytest.raises(KeyError):
        get_image(media_item, 1, str(temp_output_dir))


# =============================================================================
# Disk usage tests
# =============================================================================


@patch("childdiary_export.cli.shutil.disk_usage")
def test_check_disk_usage_sufficient_space(mock_disk_usage, temp_output_dir):
    """Test disk usage check with sufficient space."""
    mock_usage = MagicMock()
    mock_usage.used = 50 * 1024 * 1024 * 1024  # 50 GB used
    mock_usage.total = 100 * 1024 * 1024 * 1024  # 100 GB total
    mock_disk_usage.return_value = mock_usage

    result = check_disk_usage(str(temp_output_dir), threshold=90.0)
    assert result is True


@patch("childdiary_export.cli.shutil.disk_usage")
def test_check_disk_usage_insufficient_space(mock_disk_usage, temp_output_dir):
    """Test disk usage check with insufficient space."""
    mock_usage = MagicMock()
    mock_usage.used = 950 * 1024 * 1024
    mock_usage.total = 1000 * 1024 * 1024
    mock_disk_usage.return_value = mock_usage

    result = check_disk_usage(
        str(temp_output_dir),
        threshold=90.0,
        on_prompt=lambda msg: False,
    )
    assert result is False


# =============================================================================
# Compression tests
# =============================================================================


def test_compress_zip(temp_output_dir):
    """Test ZIP compression."""
    file1 = temp_output_dir / "file1.txt"
    file2 = temp_output_dir / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")

    compress_files(
        file_list=[str(file1), str(file2)],
        archive_name="test_archive",
        compress_type="zip",
    )

    zip_file = temp_output_dir / "test_archive.zip"
    assert zip_file.exists()


def test_compress_gzip(temp_output_dir):
    """Test GZIP compression."""
    file1 = temp_output_dir / "file1.txt"
    file1.write_text("content1")

    compress_files(
        file_list=[str(file1)],
        archive_name="test_archive",
        compress_type="gzip",
    )

    tar_file = temp_output_dir / "test_archive.tar.gz"
    assert tar_file.exists()


def test_compress_bz2(temp_output_dir):
    """Test BZIP2 compression."""
    file1 = temp_output_dir / "file1.txt"
    file1.write_text("content1")

    compress_files(
        file_list=[str(file1)],
        archive_name="test_archive",
        compress_type="bz2",
    )

    tar_file = temp_output_dir / "test_archive.tar.bz2"
    assert tar_file.exists()


def test_compress_empty_list(temp_output_dir):
    """Test compression with empty file list."""
    compress_files(
        file_list=[],
        archive_name="test_archive",
        compress_type="zip",
    )
    assert not (temp_output_dir / "test_archive.zip").exists()


# =============================================================================
# Authentication tests
# =============================================================================


@responses.activate
@patch("childdiary_export.cli.get_credentials")
def test_create_authenticated_session_success(mock_get_credentials):
    """Test successful authenticated session creation."""
    mock_get_credentials.return_value = ("test_user", "test_pass")

    responses.add(
        responses.POST,
        "https://app.childdiary.net/api/Account/login",
        json={"token": "test_token"},
        status=200,
    )

    session = create_authenticated_session()

    assert session is not None
    assert session.cookies is not None


@responses.activate
@patch("childdiary_export.cli.get_credentials")
def test_create_authenticated_session_failure(mock_get_credentials):
    """Test failed authenticated session creation."""
    mock_get_credentials.return_value = ("test_user", "wrong_pass")

    responses.add(
        responses.POST,
        "https://app.childdiary.net/api/Account/login",
        status=401,
        body="Invalid credentials",
    )

    with pytest.raises(RuntimeError, match="Login failed"):
        create_authenticated_session()


# =============================================================================
# Export tests
# =============================================================================


@responses.activate
@patch("childdiary_export.cli.get_credentials")
def test_export_dry_run(mock_get_credentials, temp_output_dir):
    """Test export with empty media response."""
    mock_get_credentials.return_value = ("test_user", "test_pass")

    responses.add(
        responses.POST,
        "https://app.childdiary.net/api/Account/login",
        json={"token": "test_token"},
        status=200,
    )

    responses.add(
        responses.GET,
        "https://app.childdiary.net/api/media",
        json=[],
        status=200,
    )

    success = export(
        output_dir=str(temp_output_dir),
        compress=None,
        start_page=1,
        on_progress=lambda msg: None,
        on_prompt=lambda msg: True,
    )

    assert success is True
    assert temp_output_dir.exists()


@responses.activate
@patch("childdiary_export.cli.get_credentials")
@patch("childdiary_export.cli.urllib.request.urlretrieve")
def test_export_with_mocked_media(
    mock_urlretrieve, mock_get_credentials, temp_output_dir
):
    """Test export with mocked media data."""
    mock_get_credentials.return_value = ("test_user", "test_pass")

    responses.add(
        responses.POST,
        "https://app.childdiary.net/api/Account/login",
        json={"token": "test_token"},
        status=200,
    )

    responses.add(
        responses.GET,
        "https://app.childdiary.net/api/media",
        json=[
            {
                "CreatedOn": "2025-01-01T10:00:00Z",
                "Extension": ".jpg",
                "Url": "https://example.com/media/1.jpg",
            }
        ],
        status=200,
    )

    responses.add(
        responses.GET,
        "https://app.childdiary.net/api/media",
        json=[],
        status=200,
    )

    def mock_retrieve(url, dest):
        with open(dest, "wb") as f:
            f.write(b"fake image data")

    mock_urlretrieve.side_effect = mock_retrieve

    success = export(
        output_dir=str(temp_output_dir),
        compress=None,
        start_page=1,
        on_progress=lambda msg: None,
        on_prompt=lambda msg: True,
    )

    assert success is True
    assert temp_output_dir.exists()


# =============================================================================
# CLI entry point tests
# =============================================================================


@patch("childdiary_export.cli.argparse.ArgumentParser")
def test_cli_help(mock_parser):
    """Test that --help flag works."""
    mock_parser_instance = MagicMock()
    mock_parser_instance.parse_args = MagicMock(side_effect=SystemExit(0))
    mock_parser.return_value = mock_parser_instance

    with patch.object(sys, "argv", ["childdiary_export", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            from childdiary_export.cli import main

            main()
        assert exc_info.value.code == 0


@patch("childdiary_export.cli.argparse.ArgumentParser")
def test_cli_version(mock_parser):
    """Test that --version flag works."""
    mock_parser_instance = MagicMock()
    mock_parser_instance.parse_args = MagicMock(side_effect=SystemExit(0))
    mock_parser.return_value = mock_parser_instance

    with patch.object(sys, "argv", ["childdiary_export", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            from childdiary_export.cli import main

            main()
        assert exc_info.value.code == 0


@patch("childdiary_export.cli.argparse.ArgumentParser")
@patch("childdiary_export.cli.export")
@patch("childdiary_export.cli.get_credentials")
@patch("childdiary_export.cli.urllib.request.urlretrieve")
def test_cli_main_invokes_export(
    mock_urlretrieve, mock_get_credentials, mock_export, mock_parser
):
    """Test that CLI main invokes export."""
    mock_parser_instance = MagicMock()
    mock_args = MagicMock()
    mock_args.output_dir = "/tmp/output"
    mock_args.compress = "zip"
    mock_args.start_page = 1
    mock_parser_instance.parse_args.return_value = mock_args
    mock_parser.return_value = mock_parser_instance

    mock_export.return_value = True
    mock_get_credentials.return_value = ("user", "pass")

    with patch.object(sys, "argv", ["childdiary_export"]):
        from childdiary_export.cli import main

        main()

    mock_export.assert_called_once()
