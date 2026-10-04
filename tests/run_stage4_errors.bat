@echo off

python src/main.py --vfs ".\vfs_files" --script ".\tests\scripts\stage4_error_cd.txt"

pause

python src/main.py --vfs ".\vfs_files" --script ".\tests\scripts\stage4_error_find.txt"

pause