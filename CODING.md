We use several tools to check the code. Please check that mypy and
pylint do not report any error before commiting.

```bash
$ pip3 install --upgrade mypy pylint pycodestyle autoflake
$ mypy --config-file coding/mypy.ini --strict src/webamc
$ pylint --rcfile coding/pylintrc src/webamc
$ pycodestyle --ignore=E302,W50,E722,E126,E301,E501,E711 src/webamc
$ autoflake --recursive --remove-all-unused-imports src/webamc
```
