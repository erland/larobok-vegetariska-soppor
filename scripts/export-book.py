#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import re
import yaml
import zipfile
import tempfile
import shutil

ROOT = Path(__file__).resolve().parents[1]
META = ROOT / "docs" / "export-metadata.yaml"
BUILD = ROOT / "build"
EXPORTS = ROOT / "exports"

def fail(message: str) -> None:
    print(f"FEL: {message}", file=sys.stderr)
    sys.exit(1)

def load_metadata() -> dict:
    if not META.exists():
        fail("Saknar docs/export-metadata.yaml")
    try:
        return yaml.safe_load(META.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        fail(f"Kunde inte läsa metadata: {exc}")

def validate_metadata(meta: dict) -> None:
    for key in ["title", "author", "language", "identifier", "date", "version", "chapters"]:
        if not meta.get(key):
            fail(f"Metadata saknar obligatoriskt fält: {key}")
    if meta["language"] not in ["sv", "en"]:
        fail("language måste vara sv eller en")

def validate_markdown(path: Path, text: str) -> None:
    if re.search(r"^####", text, flags=re.MULTILINE):
        fail(f"{path} innehåller H4-rubrik eller djupare rubrik")
    if text.count("```") % 2 != 0:
        fail(f"{path} innehåller ojämnt antal kodblocksmarkörer")
    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        target = match.group(1)
        if target.startswith("http"):
            continue
        if not (path.parent / target).resolve().exists():
            fail(f"{path} refererar till saknad bild: {target}")


def remove_visible_epub_toc(epub_path: Path) -> None:
    """Behåll EPUB-navigationen, men ta bort nav.xhtml ur läsflödet."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(epub_path, "r") as archive:
            archive.extractall(tmp_path)

        opf_files = list(tmp_path.glob("**/*.opf"))
        if not opf_files:
            return
        opf_path = opf_files[0]
        opf = opf_path.read_text(encoding="utf-8")
        opf = re.sub(r'\s*<itemref idref="nav"\s*/>\n?', "\n", opf)
        opf_path.write_text(opf, encoding="utf-8")

        rebuilt = epub_path.with_suffix(".tmp.epub")
        if rebuilt.exists():
            rebuilt.unlink()
        with zipfile.ZipFile(rebuilt, "w") as archive:
            mimetype = tmp_path / "mimetype"
            if mimetype.exists():
                archive.write(mimetype, "mimetype", compress_type=zipfile.ZIP_STORED)
            for path in sorted(tmp_path.rglob("*")):
                if path.is_file() and path.name != "mimetype":
                    archive.write(path, path.relative_to(tmp_path).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
        shutil.move(str(rebuilt), epub_path)


def collect_chapters(meta: dict) -> str:
    parts = []
    for chapter in meta["chapters"]:
        path = ROOT / chapter
        if not path.exists():
            fail(f"Saknar kapitel: {chapter}")
        text = path.read_text(encoding="utf-8")
        validate_markdown(path, text)
        parts.append(text.strip())
    return "\n\n".join(parts) + "\n"

def run_pandoc(meta: dict, source: Path) -> None:
    title = meta["title"]
    author = meta["author"]
    lang = "sv-SE" if meta["language"] == "sv" else "en"
    slug = meta.get("project_slug", "book")
    epub = EXPORTS / f"{slug}.epub"
    pdf = EXPORTS / f"{slug}.pdf"

    if meta.get("exports", {}).get("epub", {}).get("enabled", True):
        cmd = [
            "pandoc", str(source),
            "--from=gfm", "--to=epub3",
            "--metadata", f"title={title}",
            "--metadata", f"author={author}",
            "--metadata", f"lang={lang}",
            "--css=styles/epub.css",
            "--output", str(epub)
        ]
        cover_image = meta.get("cover_image")
        if cover_image and (ROOT / cover_image).exists():
            cmd.extend(["--epub-cover-image", cover_image])
        subprocess.run(cmd, cwd=ROOT, check=True)
        if not meta.get("exports", {}).get("epub", {}).get("include_text_toc", False):
            remove_visible_epub_toc(epub)

    if meta.get("exports", {}).get("pdf", {}).get("enabled", True):
        cmd = [
            "pandoc", str(source),
            "--from=gfm",
            "--pdf-engine=xelatex",
            "--toc", "--toc-depth=3",
            "--metadata", f"title={title}",
            "--metadata", f"author={author}",
            "--metadata", f"lang={lang}",
            "--output", str(pdf)
        ]
        try:
            subprocess.run(cmd, cwd=ROOT, check=True)
        except subprocess.CalledProcessError:
            fail("PDF-export misslyckades. Kontrollera att Pandoc och xelatex/TinyTeX/MacTeX är installerade.")

def main() -> None:
    meta = load_metadata()
    validate_metadata(meta)
    BUILD.mkdir(exist_ok=True)
    EXPORTS.mkdir(exist_ok=True)
    combined = BUILD / "book.md"
    combined.write_text(collect_chapters(meta), encoding="utf-8")
    try:
        run_pandoc(meta, combined)
    except FileNotFoundError:
        fail("Pandoc saknas. Installera Pandoc för lokal EPUB/PDF-export.")
    print("Export klar. Kontrollera mappen exports/.")

if __name__ == "__main__":
    main()
