all: cpp python

cpp: test.cpp
	g++ -shared -o libtest.so -fPIC test.cpp

python:
	python build_api.py
