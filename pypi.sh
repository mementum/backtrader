#!/bin/sh
#
# Generate pypi wheels universal package and upload
#
rm dist/*
python setup.py bdist_wheel --universal
twine upload dist/*
