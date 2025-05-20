FROM node:lts-alpine

COPY . /home/app

# set the working direction
WORKDIR /home/app

RUN npm install

RUN mkdir dist
RUN mkdir dist/teaser
RUN mkdir dist/evidence

RUN mkdir public/data
RUN mkdir public/teaser
RUN mkdir public/evidence

# start app
RUN npm run build

# start app
CMD ["npm", "run", "preview"]