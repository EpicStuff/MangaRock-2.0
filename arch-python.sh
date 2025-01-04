#!/bin/bash

yay --noconfirm --sudoloop --needed -q -S \
	python-rich \
	python-lxml \
	\
	python-pyquery python-beautifulsoup4 python-playwright python-httpx \
	python-ruamel-yaml \
	python-dateparser \
	python-pytimeparse

pip install --break-system-packages \
	epicstuff==0.1.8 \
	\
	nicegui==1.4.37 \
	requests-html2
