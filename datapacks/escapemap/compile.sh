rm -rf ./data/escapemap/function

mcscript compile -fullErr

mv ./data/escapemap/functions ./data/escapemap/function

rm .mcfunction
rm -rf "#file: ."

python ./scripts/post_compile.py

echo Done.