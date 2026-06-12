This directory contains a python package called webamc allowing to
load tex files containing latex AMC MCQ ; and submit and view them via
a web interface.

Check the [examples](examples/) directory for MCQ examples.


# Todo list

- add support for grading scales

- add support for the following macros/environments: explain

- allow the modification of more item attributes (e.g., order,
  correct) from the web interface

- add support for new item metadata
  - FOLLOWS : specify that an item always follows another one
  - PREFIX : specify that all codes of items in a specific directory
       has some prefix


# Coding

To analyse the python code:

```bash
$ pip3 install --upgrade mypy pylint pycodestyle autoflake vulture
$ mypy --config-file coding/mypy.ini --strict src/webamc
$ pylint --rcfile coding/pylintrc src/webamc
$ pycodestyle --ignore=E712,E711,E302,W50,E722 src/webamc
$ autoflake --recursive --remove-all-unused-imports src/webamc
$ vulture --exclude src/webamc/test src
```

To build the package:
```bash
$ python3 -m build
```
