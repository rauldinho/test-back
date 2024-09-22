import asyncio
import os
from flask import Flask
from models import db
from routes import init_routes
from pagerduty_sync import main
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")
print(f"Loaded SQLALCHEMY_DATABASE_URI: {
      os.getenv('SQLALCHEMY_DATABASE_URI')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
init_routes(app)


def start_app():
    """Initialize the app by resetting the database and fetching data from PagerDuty."""
    with app.app_context():
        print("Removing DB...")
        db.drop_all()

        print("Creating DB...")
        db.create_all()

        # Fetch and store data asynchronously from PagerDuty
        print("Fetching and Storing PagerDuty data started...")
        asyncio.run(main())


if __name__ == "__main__":
    with app.app_context():
        start_app()
    app.run(debug=True, port=5001, host="0.0.0.0")
