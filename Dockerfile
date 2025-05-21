FROM node:lts-alpine

COPY . /home/app

# set the working direction
WORKDIR /home/app

RUN npm install

RUN mkdir dist
RUN mkdir dist/media
RUN mkdir dist/media/data
RUN mkdir dist/media/teaser
RUN mkdir dist/media/evidence

RUN mkdir public/media
RUN mkdir public/media/data
RUN mkdir public/media/teaser
RUN mkdir public/media/evidence

# start app
RUN npm run build

# start app
CMD ["npm", "run", "preview"]