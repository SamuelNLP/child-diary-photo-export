"""Tests for the GUI module with mocked API connections."""

import os
import tkinter as tk
from unittest.mock import MagicMock, patch

import keyring.errors
import pytest

# Skip all tests if tkinter is not available
pytest.importorskip("tkinter")

from childdiary_export.gui import (
    DEFAULT_OUTPUT,
    ChildDiaryExportGUI,
    main,
)

# =============================================================================
# GUI initialization tests
# =============================================================================


def test_gui_window_title(root_window):
    """Test that GUI window has correct title."""
    ChildDiaryExportGUI(root_window)
    assert root_window.title() == "ChildDiary Photo Export"


def test_widgets_created(root_window):
    """Test that all required widgets are created."""
    app = ChildDiaryExportGUI(root_window)

    assert hasattr(app, "main_frame")
    assert hasattr(app, "output_dir_entry")
    assert hasattr(app, "compress_combo")
    assert hasattr(app, "start_page_spin")
    assert hasattr(app, "run_button")
    assert hasattr(app, "stop_button")
    assert hasattr(app, "output_text")
    assert hasattr(app, "status_var")


def test_status_bar_initial_state(root_window):
    """Test that status bar starts with 'Ready'."""
    app = ChildDiaryExportGUI(root_window)
    assert app.status_var.get() == "Ready"


# =============================================================================
# Form widget tests
# =============================================================================


def test_output_dir_widget(root_window):
    """Test that output directory widget exists."""
    app = ChildDiaryExportGUI(root_window)
    assert app.output_dir_entry is not None
    assert app.output_dir_var is not None


def test_compression_widget(root_window):
    """Test that compression widget exists."""
    app = ChildDiaryExportGUI(root_window)
    assert app.compress_combo is not None
    assert app.compress_var is not None


def test_start_page_widget(root_window):
    """Test that start page widget exists."""
    app = ChildDiaryExportGUI(root_window)
    assert app.start_page_spin is not None
    assert app.start_page_var is not None


def test_buttons_widget(root_window):
    """Test that buttons exist."""
    app = ChildDiaryExportGUI(root_window)
    assert app.run_button is not None
    assert app.stop_button is not None


# =============================================================================
# Default values tests
# =============================================================================


def test_default_output_dir(root_window):
    """Test default output directory value."""
    app = ChildDiaryExportGUI(root_window)
    assert app.output_dir_var.get() == DEFAULT_OUTPUT


def test_default_compression(root_window):
    """Test default compression value."""
    app = ChildDiaryExportGUI(root_window)
    assert app.compress_var.get() == "zip"


def test_default_start_page(root_window):
    """Test default start page value."""
    app = ChildDiaryExportGUI(root_window)
    assert app.start_page_var.get() == 1


# =============================================================================
# Compression options tests
# =============================================================================


def test_compression_menu_values(root_window):
    """Test that compression menu has expected values."""
    app = ChildDiaryExportGUI(root_window)
    values = app.compress_combo["values"]
    assert "zip" in values
    assert "gzip" in values
    assert "bz2" in values
    assert "" in values


# =============================================================================
# Browse button tests
# =============================================================================


@patch("childdiary_export.gui.filedialog.askdirectory")
def test_browse_button_opens_dialog(mock_askdirectory, root_window):
    """Test that browse button opens directory dialog."""
    mock_askdirectory.return_value = "/tmp/test"

    app = ChildDiaryExportGUI(root_window)
    app.browse_output_dir()

    mock_askdirectory.assert_called_once()


@patch("childdiary_export.gui.filedialog.askdirectory")
def test_browse_button_updates_field(mock_askdirectory, root_window):
    """Test that browse button updates output directory field."""
    test_dir = "/tmp/test_output"
    mock_askdirectory.return_value = test_dir

    app = ChildDiaryExportGUI(root_window)
    app.browse_output_dir()

    assert app.output_dir_var.get() == test_dir


@patch("childdiary_export.gui.filedialog.askdirectory")
def test_browse_button_cancels(mock_askdirectory, root_window):
    """Test browse button when user cancels dialog."""
    mock_askdirectory.return_value = None

    app = ChildDiaryExportGUI(root_window)
    initial_dir = app.output_dir_var.get()
    app.browse_output_dir()

    assert app.output_dir_var.get() == initial_dir


# =============================================================================
# Output text tests
# =============================================================================


def test_output_text_exists(root_window):
    """Test that output text area exists."""
    app = ChildDiaryExportGUI(root_window)
    assert app.output_text is not None


def test_append_to_output(root_window):
    """Test appending text to output area."""
    app = ChildDiaryExportGUI(root_window)

    app.append_output("Test message")

    app.output_text.config(state=tk.NORMAL)
    text = app.output_text.get("1.0", tk.END)

    assert "Test message" in text


def test_append_multiple_messages(root_window):
    """Test appending multiple messages to output area."""
    app = ChildDiaryExportGUI(root_window)

    app.append_output("First message")
    app.append_output("Second message")

    app.output_text.config(state=tk.NORMAL)
    text = app.output_text.get("1.0", tk.END)

    assert "First message" in text
    assert "Second message" in text


# =============================================================================
# Export button tests
# =============================================================================


@patch("childdiary_export.gui.messagebox.showerror")
def test_export_button_with_empty_output_dir(mock_showerror, root_window):
    """Test export button with empty output directory shows error."""
    app = ChildDiaryExportGUI(root_window)
    app.output_dir_var.set("")

    app.start_export()

    mock_showerror.assert_called_once()
    call_args = mock_showerror.call_args
    assert "output directory" in str(call_args).lower()


@patch("childdiary_export.gui.shutil.disk_usage")
@patch("childdiary_export.gui.messagebox.askyesno")
def test_export_button_with_low_disk_space(mock_askyesno, mock_disk_usage, root_window):
    """Test export button warns about low disk space."""
    mock_usage = MagicMock()
    mock_usage.used = 950 * 1024 * 1024
    mock_usage.total = 1000 * 1024 * 1024
    mock_disk_usage.return_value = mock_usage

    mock_askyesno.return_value = False

    app = ChildDiaryExportGUI(root_window)
    app.start_export()

    mock_askyesno.assert_called_once()


# =============================================================================
# Credentials tests
# =============================================================================


@patch.dict(
    os.environ, {"CHILD_DIARY_USERNAME": "env_user", "CHILD_DIARY_PASSWORD": "env_pass"}
)
def test_get_credentials_from_env(root_window):
    """Test getting credentials from environment variables."""
    app = ChildDiaryExportGUI(root_window)

    credentials = app.get_credentials_gui()

    assert credentials == ("env_user", "env_pass")


@patch("keyring.get_credential")
def test_get_credentials_from_keyring(mock_get_credential, root_window):
    """Test getting credentials from keyring."""
    mock_cred = MagicMock()
    mock_cred.username = "keyring_user"
    mock_cred.password = "keyring_pass"
    mock_get_credential.return_value = mock_cred

    app = ChildDiaryExportGUI(root_window)

    credentials = app.get_credentials_gui()

    assert credentials == ("keyring_user", "keyring_pass")


@patch("keyring.get_credential")
@patch("childdiary_export.gui.simpledialog.askstring")
def test_get_credentials_from_prompt(mock_askstring, mock_get_credential, root_window):
    """Test getting credentials from user prompt."""
    mock_get_credential.side_effect = keyring.errors.KeyringError("No keyring")
    mock_askstring.side_effect = ["prompted_user", "prompted_pass"]

    app = ChildDiaryExportGUI(root_window)

    credentials = app.get_credentials_gui()

    assert credentials == ("prompted_user", "prompted_pass")


@patch("keyring.get_credential")
@patch("childdiary_export.gui.simpledialog.askstring")
def test_get_credentials_cancelled(mock_askstring, mock_get_credential, root_window):
    """Test cancelled credential prompt returns None."""
    mock_get_credential.side_effect = keyring.errors.KeyringError("No keyring")
    mock_askstring.return_value = None

    app = ChildDiaryExportGUI(root_window)

    credentials = app.get_credentials_gui()

    assert credentials is None


# =============================================================================
# GUI entry point tests
# =============================================================================


@patch("childdiary_export.gui.tk.Tk")
@patch("childdiary_export.gui.ChildDiaryExportGUI")
def test_gui_main_creates_window(mock_gui, mock_tk):
    """Test that GUI main function creates a Tk window."""
    mock_root = MagicMock()
    mock_tk.return_value = mock_root

    mock_gui_instance = MagicMock()
    mock_gui.return_value = mock_gui_instance

    main()

    mock_tk.assert_called_once()
    mock_gui.assert_called_once_with(mock_root)
    mock_root.mainloop.assert_called_once()
