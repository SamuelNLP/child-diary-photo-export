"""Authentication management for ChildDiary API."""

import getpass
import os

import keyring


def get_credentials() -> tuple[str, str]:
    """Get credentials from environment variables or keyring.

    Priority:
    1. Environment variables CHILD_DIARY_USERNAME/CHILD_DIARY_PASSWORD
    2. Keyring service 'app.childdiary.net' - prompts for username if absent
    3. Interactive prompt to enter and store new credentials in keyring

    Returns
    -------
    tuple[str, str]
        (username, password)
    """
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

    # Prompt user
    username = input("ChildDiary username: ")
    password = getpass.getpass("ChildDiary password: ")

    # Store in keyring for next time
    keyring.set_password(service, username, password)

    return username, password
