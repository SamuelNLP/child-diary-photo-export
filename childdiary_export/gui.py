"""GUI wrapper for ChildDiary photo export script.

Provides a simple Tkinter interface for non-technical users to run the export
without using the command line.
"""

import os
import shutil
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import TYPE_CHECKING, Optional

import requests

from .cli import export

if TYPE_CHECKING:
    from requests import Session

# Check if we're running as a PyInstaller bundle
if getattr(sys, "frozen", False):
    # Running as bundle, use the temp folder for output
    APP_PATH = getattr(sys, "_MEIPASS", None)
    DEFAULT_OUTPUT = os.path.join(os.path.expanduser("~"), "ChildDiaryExport")
else:
    # Running in development
    APP_PATH = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_OUTPUT = os.path.join(APP_PATH, "media")


class ChildDiaryExportGUI:
    """Main GUI application for ChildDiary photo export."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the GUI.

        Parameters
        ----------
        root : tk.Tk
            The root Tkinter window.
        """
        self.root = root
        self.root.title("ChildDiary Photo Export")
        self.root.geometry("500x400")
        self.root.resizable(True, True)

        # Configure styles
        self.configure_styles()

        # Create main container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create form fields
        self.create_form()

        # Create action buttons
        self.create_buttons()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(
            self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        # Output text area for logs
        self.output_text = tk.Text(
            self.main_frame, height=8, wrap=tk.WORD, state=tk.DISABLED
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for output
        scrollbar = ttk.Scrollbar(self.output_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.output_text.yview)

        # Running state
        self.running = False

        # Cached session for background thread
        self._session: Optional["Session"] = None

    def get_credentials_gui(self) -> tuple[str, str] | None:
        """Get credentials using GUI dialogs.

        Returns
        -------
        tuple[str, str] | None
            (username, password) or None if cancelled.
        """
        import os

        import keyring

        # First check environment variables
        username = os.getenv("CHILD_DIARY_USERNAME")
        password = os.getenv("CHILD_DIARY_PASSWORD")

        if username and password:
            return username, password

        # Try keyring
        service = "app.childdiary.net"
        try:
            credential = keyring.get_credential(service, None)
            if credential and credential.username and credential.password:
                return credential.username, credential.password
        except keyring.errors.KeyringError:
            pass

        # Prompt user with GUI dialogs
        username = simpledialog.askstring("Credentials", "ChildDiary username:")
        if username is None:
            return None

        password = simpledialog.askstring(
            "Credentials", "ChildDiary password:", show="*"
        )
        if password is None:
            return None

        # Store in keyring for next time
        try:
            keyring.set_password(service, username, password)
        except keyring.errors.KeyringError:
            pass

        return username, password

    def configure_styles(self) -> None:
        """Configure custom ttk styles."""
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 11))
        style.configure("TButton", font=("Helvetica", 11))
        style.configure("TEntry", font=("Helvetica", 11))
        style.configure("TCombobox", font=("Helvetica", 11))

    def create_form(self) -> None:
        """Create the form input fields."""
        # Output Directory
        ttk.Label(self.main_frame, text="Output Directory:").pack(
            anchor=tk.W, pady=(0, 2)
        )
        self.output_dir_var = tk.StringVar(value=DEFAULT_OUTPUT)
        entry_frame = ttk.Frame(self.main_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        self.output_dir_entry = ttk.Entry(
            entry_frame, textvariable=self.output_dir_var, width=40
        )
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_button = ttk.Button(
            entry_frame,
            text="Browse...",
            command=self.browse_output_dir,
            width=10,
        )
        browse_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Compression
        ttk.Label(self.main_frame, text="Compression:").pack(anchor=tk.W, pady=(0, 2))
        self.compress_var = tk.StringVar(value="zip")
        self.compress_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.compress_var,
            values=["zip", "gzip", "bz2", ""],
            state="readonly",
            width=15,
        )
        self.compress_combo.pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(
            self.main_frame,
            text="(Leave empty to disable compression)",
            foreground="gray",
        ).pack(anchor=tk.W, pady=(0, 10))

        # Start Page
        ttk.Label(self.main_frame, text="Start Page:").pack(anchor=tk.W, pady=(0, 2))
        self.start_page_var = tk.IntVar(value=1)
        self.start_page_spin = ttk.Spinbox(
            self.main_frame,
            from_=1,
            to=999,
            textvariable=self.start_page_var,
            width=10,
        )
        self.start_page_spin.pack(anchor=tk.W, pady=(0, 10))

    def create_buttons(self) -> None:
        """Create action buttons."""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.run_button = ttk.Button(
            button_frame,
            text="Start Export",
            command=self.start_export,
            style="Accent.TButton",
        )
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = ttk.Button(
            button_frame,
            text="Stop",
            command=self.stop_export,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT)

    def browse_output_dir(self) -> None:
        """Open file dialog to select output directory."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.output_dir_var.get(),
        )
        if directory:
            self.output_dir_var.set(directory)

    def append_output(self, text: str) -> None:
        """Append text to the output area.

        Parameters
        ----------
        text : str
            Text to append.
        """
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_export(self) -> None:
        """Start the export process in a background thread."""
        if self.running:
            return

        # Validate inputs
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("Error", "Please select an output directory")
            return

        # Pre-check disk space before starting
        usage = shutil.disk_usage(output_dir)
        percent_used = (usage.used / usage.total) * 100
        if percent_used >= 90.0 and not messagebox.askyesno(
            "Low Disk Space",
            f"Disk usage is at {percent_used:.1f}%. Continue anyway?",
        ):
            return

        # Get credentials in main thread (before starting background thread)
        self.append_output("Authenticating...")
        self.root.update()

        credentials = self.get_credentials_gui()
        if credentials is None:
            self.append_output("Authentication cancelled.")
            return

        username, password = credentials

        # Create authenticated session in main thread
        try:
            import requests

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
                messagebox.showerror(
                    "Login Failed",
                    f"Login failed ({login_response.status_code}): {login_response.text}",
                )
                return

            self.append_output("Authentication successful.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Login Error", f"Failed to authenticate: {e}")
            return

        compress = self.compress_var.get()
        start_page = self.start_page_var.get()

        # Store session for background thread
        self._session = session

        # Update UI
        self.running = True
        self.run_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("Running...")
        self.append_output(f"Starting export to: {output_dir}")
        if compress:
            self.append_output(f"Compression: {compress}")
        self.append_output(f"Start page: {start_page}")
        self.append_output("-" * 40)

        # Run in background thread
        self.export_thread = threading.Thread(
            target=self.run_export,
            args=(output_dir, compress, start_page),
            daemon=True,
        )
        self.export_thread.start()

    def run_export(self, output_dir: str, compress: str, start_page: int) -> None:
        """Run the export directly using the script module.

        Parameters
        ----------
        output_dir : str
            Output directory for the export.
        compress : str
            Compression type or empty string.
        start_page : int
            Starting page number.
        """
        try:
            self.append_output("Running export...")
            self.append_output("")

            # For GUI mode, we use thread-safe callbacks
            # Progress updates are queued via root.after()
            def safe_progress(msg: str) -> None:
                """Schedule progress update on main thread."""
                self.root.after(0, lambda: self.append_output(msg))

            # Disk space is pre-checked before starting, so prompts should not occur
            # This is a fallback that auto-confirms
            def gui_prompt(msg: str) -> bool:
                """Handle prompts in GUI - auto-confirm (disk space pre-checked)."""
                self.root.after(0, lambda: self.append_output(f"WARNING: {msg}"))
                return True

            success = export(
                output_dir=output_dir,
                compress=compress if compress else None,
                start_page=start_page,
                on_progress=safe_progress,
                on_prompt=gui_prompt,
                session=self._session,
            )

            if success:
                self.append_output("")
                self.append_output("Export completed successfully!")
                self.status_var.set("Completed")
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Success", "Export completed successfully!"
                    ),
                )
            else:
                self.append_output("")
                self.append_output("Export failed")
                self.status_var.set("Failed")

        except (requests.exceptions.RequestException, OSError) as e:
            self.append_output(f"Error: {e}")
            self.append_output("")
            self.append_output("Export failed with exception")
            self.status_var.set("Error")

        finally:
            self.running = False
            self.root.after(0, self.reset_ui)

    def reset_ui(self) -> None:
        """Reset UI after export completes."""
        self.run_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Ready")

    def stop_export(self) -> None:
        """Stop the export process."""
        self.append_output("Stop requested...")
        self.status_var.set("Stopping...")
        # Note: Proper process termination would require tracking the process
        # This is a simple implementation


def main() -> None:
    """Main entry point for the GUI application."""
    root = tk.Tk()
    ChildDiaryExportGUI(root)

    # Center window on screen
    root.eval("tk::PlaceWindow . center")

    # Set minimum size
    root.minsize(450, 350)

    # Run application
    root.mainloop()


if __name__ == "__main__":
    main()
