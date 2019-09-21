#!/usr/bin/env bash
{
	sudo apt update
	sudo apt install git python3-pip

	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash # installs node version manager
	source ~/.bashrc
	nvm install node # installs the lastest version of node

	npm install webtorrent-cli -g

	pip3 install pirate-get
	export PATH=$PATH:~/.local/bin
}
