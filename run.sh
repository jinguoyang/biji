#!/bin/bash
LOCAL=`cd $(dirname $0) && pwd`
cd $LOCAL
PYTHON='.pyenv/bin/python'
SUPERVISOR='.pyenv/bin/supervisorctl'
CONFIG='../config/biji_server'

find . -name '*pyc' | xargs rm -f

$PYTHON -m py_compile server.py
$PYTHON -m py_compile logger.py

cp -r $CONFIG/*  confs/
${PYTHON} build.py
# find . -name '*py' ! -path "./.pyenv/*" | xargs rm -f
$SUPERVISOR -c confs/supervisor.conf restart all
