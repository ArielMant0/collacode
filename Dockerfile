FROM node:lts-alpine

COPY . /home/app

# set the working direction
WORKDIR /home/app

RUN npm install

# start app
RUN npm run build

# start app
CMD ["npm", "run", "preview"]