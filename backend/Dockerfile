# start by pulling the python image
FROM python:3.10-alpine

RUN apk update && apk add sqlite

# copy the requirements file into the image
COPY ./requirements.txt /backend/requirements.txt

# switch working directory
WORKDIR /backend

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /backend

RUN mkdir data

RUN sqlite3 data/data.db < db.sql

RUN python add_user.py admin admin123 -r admin

# start waitress server
CMD ["waitress-serve", "--listen=*:8000", "--threads=8" , "--call" , "server:create_app"]