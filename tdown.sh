#!/usr/bin/env bash
{
	install_nodejs() {
		curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash # installs node version manager
		. ~/.nvm/nvm.sh
		nvm install node # installs the lastest version of node

		npm install webtorrent-cli -g
	}

	sudo apt update
	sudo apt install git python3-pip

	[[ ! `command -v npm` ]] && install_nodejs
	
	pip3 install pirate-get

	[[ $PATH != *"$HOME/.local/bin"* ]] && echo -e "\nexport PATH=$PATH:~/.local/bin" >> ~/.bashrc
}
