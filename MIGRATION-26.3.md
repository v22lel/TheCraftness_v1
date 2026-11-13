# Minecraft 26.3 migration

Branch: upgrade/26.3. Fresh world folder: TheCraftness_v1_26_3.
The first branch commit snapshots the original working copy before migration.
The second contains datapack migration fixes. No world chunks were upgraded by Codex.

Git history lives outside the world in ../upgrade-diagnostics/craftness-26.3.git.
Keep that directory together with this checkout. The world contains only a writable .git pointer file.
Original world and tar.gz remain unchanged.

Changes:
- Convert advancement conditions and entity predicates to the new formats.
- Wrap item modifier files in explicit sequences, rename function to type,
  decode old JSON text strings, and migrate adventure component predicates.
- Convert block-state Name/Properties fields to id/properties in compiled
  functions, mcscript source, and elevator generator templates.
- Fix the boat slab can_place_on component.

Crash ending:
The original noise settings start at Y=336 and span 352 blocks, outside the
configured dimension range of -64 through 319. The original crash function
forces chunk generation there. The definitions also fail current registry
parsing. They remain disabled; restoring the old files blocks world loading.
Original definitions are preserved in the baseline Git commit and diagnostic
backups. The crash function remains but cannot reproduce the ending with the
dimension disabled. A reliable vanilla command to silently close the client
has not been established. Test or redesign the ending separately.

Validation:
The previous JSON fixes loaded in-game per the user's test.
The display and boat-slab fixes have only been checked statically and need
in-game verification. Reload the existing upgrade_test copy and reset/restart
the pressure-plate puzzles and elevators to spawn new display entities.
Then upgrade this fresh copy normally, with the datapack enabled from the start.
Do not save this fresh copy in safe mode: custom song references may be lost.
Check the chest at -10 -35 39 and jukebox at -9 -35 38 for challenge_theme.
A full playthrough remains necessary to find other command and asset changes.
