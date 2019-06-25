# Watchmen Project <a href="https://github.com/Infoblox-CTO" style="text-decoration:none;"><img src="https://s3-us-west-1.amazonaws.com/infobloxcdn/wp-content/uploads/2016/05/07230930/logo.png" style="border:0" height="50" alt="Infoblox" border="0" title="Infoblox" align="right" valign="top" /></a>

> internal monitoring systems



<br/><a name="contents"></a>
## Contents

* [Design](watchmen/README.md)
* [Documentation](docs/README.md)
* [Prerequisites Checklist](#pre-req)
* [Dev Setup](#dev-setup)
* [Testing](#testing)
* [Run](#run)



<br/><a name="pre-req"></a>
## Prerequisites

  * Python [3](https://www.python.org/downloads/)
  * Python 3 `pip` [version 19.0.1 and up](https://pip.pypa.io/en/stable/installing/)
  * Python 3 built-in virtual env [`venv`](https://docs.python.org/3/library/venv.html)
  * System tools: find, rm, tee, xargs, zip
  * Command line JSON processor: [jq](https://stedolan.github.io/jq/download/)
  * Docker ([optional](https://www.docker.com/))


<br/><a name="dev-setup"></a>
## Dev Setup

  Running a `dev-setup` script to install the project and libraries.

  ```
  make clean setup  # this will create a python virtualenv
  ```


<br/><a name="testing"></a>
## Testing

  After running `make dev-setup`, the project and libraries are installed (in python virtual environment). Now it is able to run tests.

  ```
  make test  # also available to run `make unittest` or `make nosetest`
  ```
  or to start a clean test (highly recommended before committing changes) -

  ```
  make clean test-all
  ```
  and open test coverage report

  ```
  make show  # must be on docker host
  ```



<br/><a name="run"></a>
## Run

### API Example

  * run Gunicorn/Flask API in docker container

    ```
    make run-api
    ```

  * run Gunicorn/Flask example in virtual environment (venv)

    ```
    # start/enable venv (e.g. `source .venv/bin/activate`)
    make run-gunicorn
    ```

  * run Gunicorn/FastApi in venv

    ```
    # start/enable venv (e.g. `source .venv/bin/activate`)
    make run-fastapi
    ```



<p><br/></p>

<div><br/>
<a href="https://github.com/Infoblox-CTO" style="text-decoration:none;"><img src="https://avatars0.githubusercontent.com/u/12451624?v=4&s=100" style="border:0;height:50;width:50px;" height="50" alt="Infoblox-CTO" border="0" title="Infoblox" align="right" valign="top" /></a>
</div>

&raquo; Back to <a href="#contents">Contents</a> | <a href="./watchmen">Design Notes</a> &laquo;
