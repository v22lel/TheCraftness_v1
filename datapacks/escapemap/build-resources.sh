#!/bin/sh
set -eu

pack_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
output_dir=${1:-"$pack_dir/../../resourcepacks"}

python3 - "$pack_dir/resources" "$output_dir" <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
import sys

source, output = (Path(arg).resolve() for arg in sys.argv[1:])
if not (source / "pack.mcmeta").is_file() or not (source / "assets").is_dir():
    sys.exit(f"Missing pack.mcmeta or assets in {source}")
if output.is_relative_to(source):
    sys.exit("Build resources.zip outside the resource pack source folder")

output.mkdir(parents=True, exist_ok=True)
destination = output / "resources.zip"
with TemporaryDirectory(dir=output) as temp:
    archive = Path(temp) / destination.name
    with ZipFile(archive, "w", ZIP_DEFLATED) as pack:
        for file in sorted(source.rglob("*")):
            if file.is_file():
                pack.write(file, file.relative_to(source))
    archive.replace(destination)

print(f"Built {destination}")
PY
