# start by pulling the python image
FROM python:3.10-alpine

ARG INIT_ADMIN_NAME
ARG INIT_ADMIN_PW
ARG BACKEND_PORT_INT

ENV INIT_ADMIN_NAME=${INIT_ADMIN_NAME}
ENV INIT_ADMIN_PW=${INIT_ADMIN_PW}
ENV BACKEND_PORT_INT=${BACKEND_PORT_INT}

RUN apk update && apk add sqlite

# copy every content from the local file to the image
COPY . /home/app/backend

# switch working directory
WORKDIR /home/app/backend

# install the dependencies and packages in the requirements file
RUN pip install -r requirements.txt

RUN mkdir data

RUN sqlite3 data/data.db < db.sql

RUN python add_user.py ${INIT_ADMIN_NAME} ${INIT_ADMIN_PW} -r admin

# start waitress server
CMD exec waitress-serve --listen=*:${BACKEND_PORT_INT} --threads=8 --call server:create_app