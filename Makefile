BIN=venv/bin/
ST_PACKAGES=$(HOME)/Library/Application Support/Sublime Text/Packages/

all: build

build: venv
	# TODO use the new command

venv: venv/requirements.txt

venv/requirements.txt: requirements.txt
	python3 -m venv venv
	$(BIN)pip install --upgrade pip
	$(BIN)pip install -r $<
	cp $< $@
