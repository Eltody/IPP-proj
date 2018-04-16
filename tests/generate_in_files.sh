#!/bin/sh

for i in $(find . -name '*.src'); do
	i=$(echo -n $i | head -c -4)
	php5.6 ../parse.php <"$i.src" >"$i.in"
done
