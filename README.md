RHESSysWeb
==========

Web tool for developing and manipulating RHESSys input datasets

Installation - Geoanalytics framework
-------------------------------------
First install the Geoanalytics framework as described in
JeffHeard/ga_cms (hosted on GitHub)

Installation - RHESSysWeb
-------------------------
### Clone from github into ga-cms directory
git clone https://github.com/RHESSys/RHESSysWeb.git

### Edit ga-cms/settings.py, adding RHESSysWeb to INSTALLED_APPS listing



Tests
-----

The RHESSysWeb project has a growing suite of tests that can be run via python's unittest module.  Tests are defined as .py modules in the `tests` directory.

These tests can be run manually:

    $ GISBASE=/usr/lib/grass64 LD_LIBRARY_PATH=$GISBASE/lib python -m unittest discover

Continuous Integration Testing
------------------------------

We are using Travis-CI (http://travis-ci.org) to host our continuous integration efforts.  Continuous integration helps us run our test suite upon every commit to this repository and let us know if and when we break the build.

The current build status is: [![Build Status](https://travis-ci.org/RHESSys/RHESSysWeb.png?branch=master)](https://travis-ci.org/RHESSys/RHESSysWeb)

The above icon should be clickable and point to the latest build at Travis-CI: https://travis-ci.org/RHESSys/RHESSysWeb

The `.travis.yml` configuration file defines how this project is hooked to Travis-CI.  Github has a post-commit hook that is fired upon every commit to this repository.  This post-commit hook uses an authentication token to login to Travis-CI and run the configured steps on a virtual machine.  A return value of 0 means success and generates a 'green' status indicator.

The indicator above may be red until the virtual machines used at Travis-CI are upgraded to Ubuntu 12.10 which includes GRASS 6.4.2 packages.  RHESSysWeb requires GRASS 6.4.2.

There are currently 2 tests that fail due to the Ubuntu 12.04 testing VM.

