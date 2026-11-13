# Inventory updates in 26.3

area/items.mcscript now contains direct /item modify commands rather than a
macro that expands into per-slot execute/modify commands. Reusable slot_source
files under data/escapemap/slot_source/inventory select slots and filter by
both item type and puzzle ID, using partial custom_data matching as before.

Coverage: hotbar, inventory, offhand, cursor, and all four player crafting slots.
Main hand is already a hotbar slot and is processed once. Armor slots, ender
chests, and nested containers are deliberately outside the original scope.
Area dispatch and inventory_changed advancement are unchanged. Drop handling,
pickup policy, item lifetimes, and area-change timing are unchanged.

Validation: ran compile.sh and post_compile.py in a temporary copy. All 2040
function paths survived. All 16 area item functions preserve the original
predicate/modifier mappings. Their 860 commands became 20. Other function
command sequences were unchanged, apart from harmless objective creation
ordering in the compiler-generated load file, which was not copied back.
Generated functions and mcscript source are both included in this commit.
Minecraft registry loading and gameplay verification remain to be done.

In-game checks after /reload: area transitions and inventory pickup; matching
and ordinary untagged items in hotbar/inventory/offhand/cursor/crafting; both
flashlight forms; ground drops acquired in valid areas. Check neutral-area
pickup behavior separately: this rewrite does not restore the commented-out
freeze/unfreeze calls.
