# FloBot Server

[![Coverage Status](https://coveralls.io/repos/github/Team9-RobotIX/AWS/badge.svg)](https://coveralls.io/github/Team9-RobotIX/AWS)
[![Build Status](https://travis-ci.org/Team9-RobotIX/AWS.svg?branch=master)](https://travis-ci.org/Team9-RobotIX/AWS)

This is the repository for the web server, running on AWS.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

To run this project, you will need Python 2.7. We recommend setting up a miniconda environment and installing the required dependencies directly to it.

Moreover, you will need to have SQLite3 installed.

### Installing

Once you have installed the required programs, follow the instructions below
to setup the development environment:

1. Clone this repository
2. Install dependencies using `pip install -r requirements.txt`
3. Copy the configuration file using `cp flaskapp/config.example.py flaskapp/config.py`

Once you've setup your development environment, you can start the server by running:

```
python flaskapp/flaskapp.py
```

## Running the tests

To run the tests, execute the following command on your terminal:

```
coverage run --source flaskapp flaskapp/tests.py
```

If you are using a virtual env, you can use this command:

```
coverage run --source flaskapp --omit '*/venv/*' flaskapp/tests.py
```

## Deployment

The website has two servers which will automatically pull changes from the development and master branches. They are `18.219.63.23/development` and `18.219.63.23/production`, respectively.
