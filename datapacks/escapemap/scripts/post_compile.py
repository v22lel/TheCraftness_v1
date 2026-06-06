from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path


WINDOWS_FORBIDDEN_CHARS = set('<>:"/\\|?*')
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def is_windows_illegal_name(name: str) -> bool:
    if not name:
        return True

    if any(ord(ch) < 32 for ch in name):
        return True

    if any(ch in WINDOWS_FORBIDDEN_CHARS for ch in name):
        return True

    if name.endswith(" ") or name.endswith("."):
        return True

    stem = name.split(".", 1)[0].upper()
    if stem in WINDOWS_RESERVED_NAMES:
        return True

    return False


def remove_stray_piler_lines(root: Path) -> int:
    fixed_count = 0

    for load_file in root.glob("data/*/function/mcscript/load.mcfunction"):
        try:
            original = load_file.read_text(encoding="utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            print(f"[WARN] Could not read as UTF-8: {load_file}")
            continue

        fixed = [
            line for line in original
            if line.strip() != "piler!"
        ]

        if fixed != original:
            load_file.write_text("".join(fixed), encoding="utf-8")
            fixed_count += 1
            print(f"[FIXED] Removed stray `piler!` line from: {load_file}")

    return fixed_count


def delete_path(path: Path, dry_run: bool) -> bool:
    if dry_run:
        print(f"[DRY RUN] Would delete illegal path: {path}")
        return True

    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()

        print(f"[DELETED] Illegal path: {path}")
        return True

    except Exception as exc:
        print(f"[ERROR] Failed to delete {path}: {exc}")
        return False


def remove_windows_illegal_paths(root: Path, dry_run: bool) -> int:
    deleted_count = 0

    for current_dir, dir_names, file_names in os.walk(root, topdown=False):
        current = Path(current_dir)

        for file_name in file_names:
            if is_windows_illegal_name(file_name):
                if delete_path(current / file_name, dry_run):
                    deleted_count += 1

        for dir_name in dir_names:
            if is_windows_illegal_name(dir_name):
                if delete_path(current / dir_name, dry_run):
                    deleted_count += 1

    return deleted_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply post-compile fixes to a Minecraft datapack."
    )

    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Datapack root folder. Defaults to current directory."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be deleted, but do not modify files."
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()

    if not root.exists():
        print(f"[ERROR] Root path does not exist: {root}")
        return 1

    if not root.is_dir():
        print(f"[ERROR] Root path is not a directory: {root}")
        return 1

    print(f"[INFO] Running post-compile fixes in: {root}")

    piler_fixed = remove_stray_piler_lines(root)
    illegal_deleted = remove_windows_illegal_paths(root, args.dry_run)

    print()
    print("[DONE]")
    print(f"load.mcfunction files fixed: {piler_fixed}")
    print(f"illegal paths {'found' if args.dry_run else 'deleted'}: {illegal_deleted}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())