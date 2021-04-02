BIN=venv/bin/
ST_PACKAGES=$(HOME)/Library/Application Support/Sublime Text/Packages/

all: docs install_package

docs: venv convert/*.py
	$(BIN)python convert/convert.py

venv: venv/requirements.txt

venv/requirements.txt: requirements.txt
	python3 -m venv venv
	$(BIN)pip install --upgrade pip
	$(BIN)pip install -r $<
	cp $< $@

install_package: package_deps
	ln -sf $(realpath hyperhelpcore/all/hyperhelpcore) "$(ST_PACKAGES)"
	ln -sf $(realpath .) "$(ST_PACKAGES)"
	subl --command satisfy_dependencies
	echo "You should restart ST once or twice, and then it should work."

package_deps:
	git submodule update --init
