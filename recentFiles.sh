# echo $0 $1 $2 $#
# $0 -> directory
# $1 -> file extensions separated by |
if [[ $# -eq 0 ]]; then
	ext="modules|inc|js"
fi
fileregex=".*\.($2)$"
cd $1 # avoid repeating the same parent directory
echo $1

find . -regextype posix-egrep -regex $fileregex -printf '%a %p\n' | sort -r | head -n 30 |
while read -r a b c d e f; do
        time=$(TZ=Asia/Kolkata date -d "$a $b $c $d $e PDT" +"%a %b %d %r %Y %Z")
        echo "${CYAN}$time${NC} $f"
done
