#!/bin/bash

yay --noconfirm --sudoloop --needed -q -S \
	python-rich \
	python-lxml \
	python-socketio python-aiohttp python-fastapi python-watchfiles python-aiofiles python-docutils python-httptools python-itsdangerous python-markdown2 python-markupsafe python-uvloop python-wsproto \
	python-pyquery python-beautifulsoup4 python-httpx python-playwright \
	python-ruamel-yaml \
	python-dateparser \
	python-pytimeparse

pip install --break-system-packages \
	epicstuff==0.1.8 \
	\
	nicegui==1.4.23 \
	requests-html2
