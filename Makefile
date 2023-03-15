init:
	pip install -r requirements.txt -e ./

test:
	nosetests tests
