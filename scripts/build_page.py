#!/usr/bin/env python3
"""Build static GitHub.io page using Jinja2 templates."""

import json
from datetime import UTC, datetime
from pathlib import Path

import jinja2
import requests

# Configuration
REPO = "SamuelNLP/child-diary-photo-export"
GITHUB_API = f"https://api.github.com/repos/{REPO}/releases"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent / "_site"

# Icon SVG
ICON_SVG = Path(__file__).parent.parent / "resources" / "icon.svg"


def detect_platform(asset_name):
    """Detect platform from asset name and return tuple of (platform, icon, label)."""
    name = asset_name.lower()

    if "macos" in name or "dmg" in name:
        return "macos", "🍎", "macOS"
    elif "windows" in name or "msi" in name or "exe" in name:
        return "windows", "🪟", "Windows"
    elif "linux" in name or "tar" in name or "appimage" in name:
        return "linux", "🐧", "Linux"

    return "unknown", "📦", "Download"


def format_bytes(size):
    """Format bytes to human-readable string."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def first_line(text):
    """Return first line of text."""
    return text.split("\n")[0] if text else ""


def truncate(text, length=200):
    """Truncate text to given length."""
    return text[:length]


def date_format(value, format="%b %d, %Y"):
    """Format date string."""
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        return dt.strftime(format)
    except ValueError, TypeError:
        return value


def main():
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PT_DIR = OUTPUT_DIR / "pt"
    PT_DIR.mkdir(parents=True, exist_ok=True)

    # Set up Jinja2 environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register custom filters
    env.filters["first_line"] = first_line
    env.filters["truncate"] = truncate
    env.filters["date_format"] = date_format

    # Read icon SVG
    icon_svg = ICON_SVG.read_text()

    # Fetch releases from GitHub
    try:
        response = requests.get(GITHUB_API, timeout=10)
        response.raise_for_status()
        releases = response.json()

        # Filter releases with assets, sort by date, take latest 3
        releases = [r for r in releases if r.get("assets")]
        releases.sort(key=lambda r: r["published_at"], reverse=True)
        releases = releases[:3]

        # Enrich assets with platform info
        for release in releases:
            for asset in release.get("assets", []):
                platform, icon, label = detect_platform(asset["name"])
                asset["platform"] = platform
                asset["icon"] = icon
                asset["label"] = label
                asset["size_formatted"] = format_bytes(asset["size"])

    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Warning: Could not fetch releases: {e}")
        releases = []

    # Translations
    translations = {
        "en": {
            "tagline": "Save your ChildDiary photos easily",
            "description": "A simple tool to download and save all your photos from ChildDiary app.",
            "latest_releases": "Latest Releases",
            "no_releases": "No releases available yet.",
            "how_to_use": "How to Use",
            "instructions": [
                "Download the executable for your operating system (Windwos, macOS, Linux)",
                "Run the application",
                "Select output directory and options",
                "Enter your ChildDiary credentials when prompted",
                "Start the export!",
            ],
            "features": "Features",
            "features_list": [
                "Export all media from ChildDiary",
                "Optional compression (zip, gzip, bz2)",
                "Resume from specific page",
                "Secure credential storage via keyring",
            ],
            "repo": "Contribute on GitHub",
            "privacy_policy": "Privacy Policy",
        },
        "pt": {
            "tagline": "Guarde as suas fotos do ChildDiary facilmente",
            "description": "Uma ferramenta simples para transferir e guardar todas as suas fotos da app ChildDiary.",
            "latest_releases": "Últimas Versões",
            "no_releases": "Nenhuma versão disponível ainda.",
            "how_to_use": "Como Usar",
            "instructions": [
                "Transfira o executável correspondente ao seu sistema operativo (Windows, macOS, Linux)",
                "Execute a aplicação",
                "Seleccione a pasta de destino e opções",
                "Introduza as suas credenciais do ChildDiary quando solicitado",
                "Inicie a exportação!",
            ],
            "features": "Funcionalidades",
            "features_list": [
                "Exportar todos os media do ChildDiary",
                "Compressão opcional (zip, gzip, bz2)",
                "Retomar de uma página específica",
                "Armazenamento seguro de credenciais via keyring",
            ],
            "repo": "Código no GitHub",
            "privacy_policy": "Política de Privacidade",
        },
    }

    # Render English page
    template = env.get_template("index.html")
    en_html = template.render(
        lang="en",
        css_path="style.css",
        icon_svg=icon_svg,
        releases=releases,
        translations=translations["en"],
        en_link="index.html",
        pt_link="pt/index.html",
        privacy_link="privacy.html",
    )
    (OUTPUT_DIR / "index.html").write_text(en_html)

    # Render Portuguese page
    pt_html = template.render(
        lang="pt",
        css_path="../style.css",
        icon_svg=icon_svg,
        releases=releases,
        translations=translations["pt"],
        en_link="../index.html",
        pt_link="index.html",
        privacy_link="privacy.html",
    )
    (PT_DIR / "index.html").write_text(pt_html)

    # Copy CSS
    css_template = env.get_template("style.css")
    css = css_template.render()
    (OUTPUT_DIR / "style.css").write_text(css)
    (PT_DIR / "style.css").write_text(css)

    # Copy privacy policy pages
    import shutil

    shutil.copy(TEMPLATES_DIR / "privacy_en.html", OUTPUT_DIR / "privacy.html")
    shutil.copy(TEMPLATES_DIR / "privacy_pt.html", PT_DIR / "privacy.html")

    print(f"Generated static pages in {OUTPUT_DIR.absolute()}")
    print(f"English: {OUTPUT_DIR / 'index.html'}")
    print(f"Portuguese: {PT_DIR / 'index.html'}")
    print(f"Privacy Policy (EN): {OUTPUT_DIR / 'privacy.html'}")
    print(f"Privacy Policy (PT): {PT_DIR / 'privacy.html'}")
    print(f"Releases: {len(releases)} release(s)")


if __name__ == "__main__":
    main()
