init:
	pip install -r requirements.txt -e ./

test:
	python -m coverage run --omit="*/test*" -m unittest -b

coverage-report:
	python -m coverage report --omit="*/test*" 
	
coverage-xml:
	python -m coverage xml --omit="*/test*" 

coverage-html:
	python -m coverage html --omit="*/test*" 

docs:
	cd docs && make clean && make html

build:
	python -m build

.PHONY: docs
