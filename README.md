# Airport API Service
The Airport API Service is a Django REST framework-based project designed to track flights from airports worldwide. This API allows you to retrieve information about airports, airplanes, flights, routes and crew members, making it a valuable tool for managing and analyzing flight data. Registered user can make an order for few or more flight tickets.

## Features
- JWT authentication
- Admin panel
- Comfortable documentation
- Managing orders and tickets
- Creating airport, crew, airplane type, route, airplane, flights
- Filtering airplane by name and flights by source and destination
- Throttling
- Pagination
- Docker and docker-compose
- PostgreSQL
- Permissions

## Run with docker
Docker should be installed
```sh
# Clone the repository
git clone https://github.com/taras-tkachuk/Airport-API-Service
# Change to the project directory
cd Airport-API-Service
# set environmental variables
create .env file and configure a .env file using a example.env template.
# build docker compose
docker-compose build
# then start containers
docker-compose up
# Open the project in your web
# Go to http://127.0.0.1:8001/
```

## Getting access
***Unauthorized** users can only view information.*

***Authorized** users can only create orders.*

***Admins** can add a record to all endpoints*
- Create a superuser account:
```sh
# open terminal inside container
docker exec -it container-name sh
# create super user
python manage.py createsuperuser
```
- get access token via api/user/token/

## Full documentation
Download: http://127.0.0.8001/api/doc/

Read: http://127.0.0.1:8001/api/doc/swagger/

## Demo
![Interface](https://snipboard.io/SEJ3kx.jpg)
