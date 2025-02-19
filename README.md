# Collacode

[<img alt="Linting status of master" src="https://img.shields.io/github/actions/workflow/status/ArielMant0/collacode/linter.yml?label=Linter&style=for-the-badge" height="23">](https://github.com/marketplace/actions/super-linter)
[<img alt="Licence" src="https://img.shields.io/github/license/ArielMant0/collacode?style=for-the-badge" height="23">](https://github.com/ArielMant0/collacode/blob/main/LICENSE)
<!-- [<img alt="Version" src="https://img.shields.io/github/v/release/ArielMant0/collacode?style=for-the-badge" height="23">](https://github.com/ArielMant0/collacode/releases/latest) -->

## Description

Collacode is a web-based tool for collaborative coding. See [GitHub Pages](https://arielmant0.github.io/collacode/) for a demo.

## Table of Contents

- [Collacode](#collacode)
  - [Description](#description)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

Download the code from this repository.

To setup the frontend, simply install the required node packages using the package manager of your choice.

```bash
# setup with npm
npm install

# setup with yarn
yarn install
```

For the backend, you need to install the packages listed in `environment.yml`, for example using conda.

```bash
conda env create -n <name>  -f environment.yml
```

To prepare the SQL database for the backend, you can use [caribou](https://github.com/clutchski/caribou) and the migration scripts provided in `backend/migrations`.
Simply create an empty SQL database and run the following command.

```bash
caribou upgrade <database-path> migrations
```

As of now, new users need to be created manually via command line. To do so, you need to run the `add_user.py` script like so:

```bash
python add_user.py -n "myusername" -p "mypassword" [-r "admin|collaborator"] [-e "my@email.com"] 
```

If you do not specify a role, the user will be added as a **collaborator**.

## Usage

CollaCode uses the standard VITE server for the frontend and a flask server for the backend. To use the out-of-the-box solution, simply start both serves like so:


Debug Configuration

```bash
# backend flask server
# set DEBUG = True in config.py
cd backend
python server.py

# frontend dev server using npm
npm run dev

# frontend dev server using yarn
yarn dev
```

Production Configuration

```bash
# backend flask server
# set DEBUG = False in config.py
cd backend
python server.py

# frontend dev server using npm
npm run build
npm run preview

# frontend dev server using yarn
yarn build
yarn preview
```

## Contributing

If you find any bugs feel free to create an issue.

## License

This project is licensed under the [MIT License](LICENSE).
