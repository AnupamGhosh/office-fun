cd $LOGS
tailf error.log |
while read -r a b c d e f g; do
        time=$(TZ=Asia/Kolkata date -d "$b $c $d PDT" +"%a %b %d %r %Y %Z")
        msg=$(echo "$g" | sed -e 's/#012/\n/g')
        echo "${CYAN}$time${NC} $msg"
done
