#!/usr/bin/env python3

# Do an automatic git pull in the current directory

import os

os.system("git fetch --all &>> auto_git_pull.log")
os.system("git reset --hard origin/master &>> auto_git_pull.log")
os.system("git pull origin master &>> auto_git_pull.log")

