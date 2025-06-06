# CollaCode

[<img alt="Linting status of master" src="https://img.shields.io/github/actions/workflow/status/ArielMant0/collacode/linter.yml?label=Linter&style=for-the-badge" height="23">](https://github.com/marketplace/actions/super-linter)
[<img alt="Licence" src="https://img.shields.io/github/license/ArielMant0/collacode?style=for-the-badge" height="23">](https://github.com/ArielMant0/collacode/blob/main/LICENSE)
<!-- [<img alt="Version" src="https://img.shields.io/github/v/release/ArielMant0/collacode?style=for-the-badge" height="23">](https://github.com/ArielMant0/collacode/releases/latest) -->

[collacode-tour.webm](https://github.com/user-attachments/assets/0af7108f-4996-4ad3-bfad-388c57ef27fb)

## Description

CollaCode is a web-based tool for collaborative coding. See [GitHub Pages](https://arielmant0.github.io/collacode/) for a (limited) demo.

To get a full demo you can visit [https://www2.visus.uni-stuttgart.de/collacode/](https://www2.visus.uni-stuttgart.de/collacode/).


## Related Publications

Short paper describing the CollaCode system design.
>F. Becker, R. P. Warnking, and T. Blascheck. *Seamless Collaborative Coding with Visualization*. EuroVis 2025 Short Papers.

Full paper where CollaCode was used to code video games and investigate externalizations.
>F. Becker, R. P. Warnking, H. Brückler, and T. Blascheck. *Beyond Entertainment: An Investigation of Externalization Design in Video Games*. EuroVis 2025. doi: [10.1111/cgf.70124](https://doi.org/10.1111/cgf.70124)

Workshop contribution for the **VisGames** workshop.
>F. Becker, R. P. Warnking, and T. Blascheck. *Playing with Knowledge: Leveraging Visualization Games for Data Validation and Inspiration*. EuroVis 2025 VisGames Workshop.

## Where To Find the Data

The data as it is used for the demo (excluding images) can be found in the `public/data/1` folder and it is available as part of the supplemental material at [https://osf.io/fhgm6/](https://osf.io/fhgm6/).

## Table of Contents

- [CollaCode](#collacode)
  - [Description](#description)
  - [Related Publications](#related-publications)
  - [Where To Find the Data?](#where-to-find-the-data)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

Download the code from this repository. Then you can either run the system on your machine directly or use docker to build a container.

### Manual Setup

To setup the frontend, simply install the required node packages using the package manager of your choice.

```bash
# setup with npm
npm install

# setup with yarn
yarn install
```

For the backend, you need to install the packages listed in `environment.yml`, for example using [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html).

```bash
conda env create -n <name>  -f environment.yml
```

Then you need to create a config file for the backend server. You may use the file `config_template.py` as a guide.

```python
DATABASE_PATH = "SET YOUR DATABASE FILENAME HERE"
SECRET_KEY = "SET YOUR SECRET KEY HERE"
SESSION_COOKIE_DOMAIN = "SET YOUR SESSION COOKIE DOMAIN HERE"
REMEMBER_COOKIE_DOMAIN = "SET YOUR REMEMBER COOKIE DOMAIN HERE"
REMEMBER_COOKIE_PATH = "/"
REMEMBER_COOKIE_SECURE = False
DEBUG = False
MAX_CONTENT_LENGTH = 5 * 1024 * 1024
```

To prepare the SQL database for the backend, you can use [caribou](https://github.com/clutchski/caribou) and the migration scripts provided in `backend/migrations`.
Simply create an empty SQL database and run the following command.

```bash
caribou upgrade <database-path> migrations
```

You can create new users manually via command line or do so in the **admin panel** of the application. To do so, you need to run the `add_user.py` script like so:

```bash
python add_user.py "username" "password" [-r "admin|collaborator"] [-e "my@email.com"]
```

If you do not specify a role, the user will be added as a **collaborator**.

## Usage

CollaCode uses the standard VITE server for the frontend and a flask server for the backend.
To use the out-of-the-box solution, simply start both serves like so:


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
