#!/bin/sh
virtualenv env
. env/bin/activate
pip install -r requirements_test.txt
