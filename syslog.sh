cd $LOGS
tailf drupal.log | grep --line-buffered anupam_debug |
while read -r a b c d e f g; do
        time=$(TZ=Asia/Kolkata date -d "$a $b $c PDT" +"%a %b %d %r %Y %Z")
        msg=$(echo "$g" | sed -e 's/#012/\n/g')
        echo "${CYAN}$time${NC} $msg"
done
