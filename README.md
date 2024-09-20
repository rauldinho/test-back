# PagerDuty Data Analysis & Visualization

This Flask application provides insights into your PagerDuty data through data synchronization, CSV reporting, and an API endpoint with Chart.js visualization.

## Features

-   **Data Synchronization:** Fetches services, incidents, teams, and escalation policies from PagerDuty and stores them in a MySQL database.
-   **CSV Reports:**
    -   Total number of services.
    -   Number of incidents per service.
    -   Number of incidents by service and status.
    -   Number of teams and their related services.
    -   Number of escalation policies and their relationships with teams and services.
-   **API Endpoint:** `/data` returns JSON data about the service with the most incidents and a breakdown of its incidents by status.
-   **Chart.js Visualization:** Displays a bar chart showcasing the incident status breakdown for the service with the most incidents.

## Setup

1.  **Clone the repository:**

`git clone https://github.com/rauldinho/test_back`

`cd test_back`

3.  **Set up environment variables:**

    Rename the `env.sample` file to `.env` in the project root directory. Add the following variables, replacing placeholders with your actual values:

    ```
        SQLALCHEMY_DATABASE_URI =
        PAGERDUTY_API_URL =
        PAGERDUTY_API_KEY =
    ```

4.  **Set up the database:**
    If you are running the application locally with a local db, update the `SQLALCHEMY_DATABASE_URI` in the `.env` to use it. For examples:

    -   Using a local sqlite:
        `sqlite:///database.db`
    -   Using local mysql (_Create the DB first and update the name in the Docker compose file_):
        `mysql://<user>:<password>@<host>/<db_name>`
    -   Using docker:
        _Any change in the DB configuration, update the Docker-compose file_

5.  **Run the application:**
    _To run the application locally:_

    -   Create a virtual environment: `py -m venv .venv`
    -   Activate it: `.\.venv\Scripts\activate`
    -   Install dependencies: `pip install -r requirements.txt`
    -   Run the application: `py app.py`

    _To run the application using Docker:_
    `docker-compose up --build `

    In both cases, the application will be accessible at [http://127.0.0.1:5001/](http://127.0.0.1:5001/).

## Usage

1.  **Main Page:** Visit [http://127.0.0.1:5001/](http://127.0.0.1:5001/) to see basic data and the incident breakdown chart.
2.  **CSV Downloads:** Use the menu option in the dashboard to download the desired CSV report.
3.  **API Endpoint:** Access `/service_with_most_incidents` to get JSON data about the service with the most incidents.

## Improvements

-   Implement a caching feature for the responses, reducing time fetching and storing the data from the API and DB. This could be implemented using [Flask Caching](https://flask-caching.readthedocs.io/en/latest/)
