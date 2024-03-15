#!/bin/sh

retval=0
for file in $(find . -type f -name "*.tex"); do
	i=1
	while IFS="" read -r line; do
		if printf "%s" "$line" | grep -P '\t' > /dev/null; then
			echo "$file:$i Use of tabs! \"$line\"" >&2
			retval=1
		fi

		if printf "%s" "$line" | grep -P '[\t ]$' > /dev/null; then
			echo "$file:$i Trailing whitespace! \"$line\"" >&2
			retval=1
		fi

		if [ $(printf "%s" "$line" | wc -m) -gt 100 ]; then
			echo "$file:$i Column limit of 100 surpassed! \"$line\"" >&2
			retval=1
		fi

		i=$(($i + 1))
	done < "$file"
done

exit $retval
