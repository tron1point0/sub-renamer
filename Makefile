PYTHON=python3.9

test: sub-renamer.py
	$(PYTHON) -m doctest -o NORMALIZE_WHITESPACE -v "$^"

deploy: sub-renamer.py
	scp "$^" vega:~/bin/

venv:
	$(PYTHON) -m venv "$@"

clean:
	-rm -r venv
	-rm -r __pycache__
