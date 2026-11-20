#!/bin/sh
set -eu

pack_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
# Default to the Minecraft instance containing this save. Pass a directory
# explicitly when working outside that instance.
local_packs=${1:-"$pack_dir/../../../../resourcepacks"}
exec "$pack_dir/build-resources.sh" "$local_packs"
