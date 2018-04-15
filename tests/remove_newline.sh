#!/bin/sh

for i in $(find . -name '*.rc'); do
	cp "$i" "$i.nl"
	grep '^' "$i.nl" | head -c-1 - >"$i"
	rm "$i.nl"
done
