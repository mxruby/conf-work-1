@echo off

python src/main.py --vfs ".\vfs_files" --script ".\tests\scripts\stage5_error_cp_args.txt"

pause

python src/main.py --vfs ".\vfs_files" --script ".\tests\scripts\stage5_error_mv_args.txt"

pause

python src/main.py --vfs ".\vfs_files" --script ".\tests\scripts\stage5_error_destination.txt"

pause

python src/main.py --vfs ".\vfs_files" --script ".\tests\scripts\stage5_error_not_found.txt"

pause