# .bash_profile

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

# User specific environment and startup programs

PATH=$HOME/.local/bin:$PATH

export PATH

# Colors
export NC=`echo -e '\e[0m'`
export CYAN=`echo -e '\e[0;36m'`
export PURPLE=`echo -e '\e[0;35m'`
export YELLOW=`echo -e '\e[1;33m'`
export LPURPLE=`echo -e '\e[1;35m'`
export BROWN=`echo -e '\e[0;33m'`

# PS1='[${BROWN}\u@\h${NC} ${PURPLE}\w${NC}]\$ '
PS1='[\[${BROWN}\]\u@\h\[${NC}\] \[${PURPLE}\]\w\[${NC}\]]\$ '

#
test=/data/var/www/vhosts/test.cozeva.com
export LOGS=$test/logs
export ALL=$test/htdocs/sites/all
export ARWMODULES=$ALL/modules/arwmodules
export LHC_WEB=$test/htdocs/cozeva_chat/lhc_web
export HTDOCS=$test/htdocs
export DNODE=$test/htdocs/drupal-node.js
