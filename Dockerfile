FROM node:lts-alpine

# set the working direction
WORKDIR /app

# install app dependencies
COPY package.json /app

# Fix permissions for packages
# RUN npm config set unsafe-perm true

RUN npm install

# Bundle app source
COPY . /app

RUN mkdir public/data
RUN mkdir public/teaser
RUN mkdir public/evidence

# start app
RUN npm run build

# start app
CMD ["npm", "run", "preview"]