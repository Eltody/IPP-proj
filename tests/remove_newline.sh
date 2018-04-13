#!/bin/sh

for i in $(find . -name '*.out'); do
	#echo "$i";	
	cp "$i" "$i.nl"
	grep '^' "$i.nl" | head -c-1 - >"$i"
	rm "$i.nl"
done

for i in $(find . -name '*.rc'); do
	#echo "$i";	
	cp "$i" "$i.nl"
	grep '^' "$i.nl" | head -c-1 - >"$i"
	rm "$i.nl"
done
