last=$(date +%s)
inotifywait -m -r -e CREATE -e MODIFY --format '%e %f' . |
while read event file; do
	current=$(date +%s)
	if [[ ( "$file" =~ .*(js|css)$ ) && ( $current-$last -gt 10 ) ]]; then
		last=$current
		cclr
	fi	
done
