# AWS

[![Coverage Status](https://coveralls.io/repos/github/Team9-RobotIX/AWS/badge.svg?branch=master)](https://coveralls.io/github/Team9-RobotIX/AWS?branch=master)
[![Build Status](https://travis-ci.org/Team9-RobotIX/AWS.svg?branch=master)](https://travis-ci.org/Team9-RobotIX/AWS)

This is the repository for the web server, running on AWS.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

To run this project, you will need Python 2.7.

### Installing

Once you have installed the required programs, follow the instructions below
to setup the development environment:

1. Clone this repository
2. Install dependencies using `pip install -r requirements.txt`

One you've setup your development environment, you can start the server by running:

```
export FLASK_APP=flaskapp/flaskapp.py
flask run
```

## Running the tests

TODO

## Deployment

The website has two servers which will automatically pull changes from the development and master branches. They are `18.219.63.23/development` and `18.219.63.23/production`, respectively.
