# Maestro

![maestro logo](./common/static/common/img/logo/maestro_background.svg)

Maestro is a multi-purpose tool for data gathering, processing, classification and providing.
It allows users to create **search contexts**, configurable structures that when executed are able to gather data from multiple sources from the internet (e.g.: Bing, Twitter), enhance and/or remove irrelevant data, classify through a classification mechanism (like a machine learning model) and finally send the results to an external service that exposes an HTTP endpoint.

This work was created and developed during [@amserra](https://github.com/amserra) Master's dissertation. To read more about Maestro, you can read the published paper [here](https://aisel.aisnet.org/cgi/viewcontent.cgi?article=1420&context=isd2014).

# Installation

The following procedures show how to install Maestro in your local machine.

## Prerequisites

Before installing Maestro you first need to have:

1. [Python](https://www.python.org/) version 3.x
2. [RabbitMQ](https://www.rabbitmq.com/) (for the Celery message broker)
3. [Git](https://git-scm.com/)
4. [PostgreSQL](https://www.postgresql.org/) (for the database)
5. [Node.JS](https://nodejs.org/en/) (to build TailwindCSS styles)

## Install

### Clone the repo

`git clone https://github.com/amserra/Maestro.git`

### Change directory to Maestro

`cd Maestro/`

### Install dependencies

`pip install -r requirements/dev.txt`

### Create database

Enter PostgreSQL interactive terminal

`psql`

Then issue the command to create the database

`CREATE DATABASE maestro_db;`

Exit the interactive terminal with CTRL+D or equivalent

### Make the migrations and migrate

`python manage.py makemigrations && python manage.py migrate`

### Install TailwindCSS dependencies

`python manage.py tailwind install`

## Develop

To develop, you need 3 terminals:

1. `python manage.py runserver`, the Django server
2. `celery -A maestro worker -l INFO`, the Celery worker
3. `python manage.py tailwind start`, the TailwindCSS dev server
