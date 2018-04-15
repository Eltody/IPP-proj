#!/bin/sh

php5.6 test.php --directory="tests/shared/jirka" --recursive >results.html

#php5.6 parse.php <.src >.in
#python3.6 interpret.py --source=".in"
