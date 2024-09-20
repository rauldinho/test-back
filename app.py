import asyncio
import os
import csv
import io
from flask import Flask, render_template, Response, abort, jsonify
from models import db, Service, Incident, Team, EscalationPolicy
from pagerduty_sync import fetch_and_store_data
from sqlalchemy import func
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")
print(f"Loaded SQLALCHEMY_DATABASE_URI: {
      os.getenv('SQLALCHEMY_DATABASE_URI')}")

app = Flask(__name__)

# Configure Flask to connect to the database using environment variables
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def start_app():
    """Initialize the app by resetting the database and fetching data from PagerDuty."""
    with app.app_context():
        print("Removing DB...")
        db.drop_all()

        print("Creating DB...")
        db.create_all()

        # Fetch and store data asynchronously from PagerDuty
        print("Fetching and Storing PagerDuty data started...")
        asyncio.run(fetch_and_store_data())


@app.route("/")
def index():
    """
    Index route that renders a page with services, incidents, teams, escalation policies,
    and details of the service with the most incidents and their status breakdown.
    """

    try:
        # Fetching all services, incidents, teams, and escalation policies from the database
        services = db.session.query(Service).all()
        incidents = db.session.query(Incident).all()
        teams = db.session.query(Team).all()
        escalation_policies = db.session.query(EscalationPolicy).all()

        # Query for the service with the most incidents
        service_most_incidents = db.session.query(
            Service,
            func.count(Incident.id).label('incident_count')
        ).join(Incident).group_by(Service.id).order_by(func.count(Incident.id).desc()).first()

        if service_most_incidents is None:
            return jsonify({"message": "No services have incidents"}), 404

        service, incident_count = service_most_incidents
        incidents = Incident.query.filter_by(service_id=service.id).all()

        # Breakdown of incidents by status for the service with the most incidents
        incident_status_breakdown = {}
        for incident in incidents:
            status = incident.status
            if status not in incident_status_breakdown:
                incident_status_breakdown[status] = 0
            incident_status_breakdown[status] += 1

        # Pass all data to the template
        data = {
            "services": services,
            "incidents": incidents,
            "teams": teams,
            "escalation_policies": escalation_policies,
            "service_most_incidents": {
                "service_id": service.id,
                "service_name": service.name,
                "total_incidents": incident_count,
                "incident_status_breakdown": incident_status_breakdown
            }
        }

        return render_template("index.html", data=data)
    except Exception as e:
        # Catch and log any exception
        return jsonify({"error": "An error occurred", "details": str(e)}), 500


@app.route("/download_csv/<string:id>")
def download_csv(id):
    """
    Route to generate and download a CSV file based on the given 'id' parameter.
    Each 'id' corresponds to a different type of CSV report.
    """
    try:
        if id == "total_services":
            # Query the total number of services
            total_services = Service.query.count()
            fieldnames = ["total_services"]
            data = [{"total_services": total_services}]

        elif id == "incidents_per_service":
            # Query the number of incidents per service
            services = Service.query.all()
            data = []
            for service in services:
                incident_count = Incident.query.filter_by(
                    service_id=service.id).count()
                data.append({
                    "service_id": service.id,
                    "service_name": service.name,
                    "incident_count": incident_count
                })
            fieldnames = ["service_id", "service_name", "incident_count"]

        elif id == "total_incidents":
            # Query all incidents with their service name and status
            incidents = Incident.query.join(
                Service, Incident.service_id == Service.id).all()
            data = []
            for incident in incidents:
                data.append({
                    "incident_id": incident.id,
                    "incident_title": incident.title,
                    "service_name": incident.service.name,
                    "incident_status": incident.status
                })
            fieldnames = ["incident_id", "incident_title",
                          "service_name", "incident_status"]

        elif id == "total_teams":
            # Query all teams and their associated services
            teams = Team.query.all()
            data = []
            for team in teams:
                for service in team.services:
                    data.append({
                        "team_id": team.id,
                        "team_name": team.name,
                        "service_id": service.id,
                        "service_name": service.name
                    })
            fieldnames = ["team_id", "team_name", "service_id", "service_name"]

        elif id == "total_escalation_policies":
            # Query all escalation policies with their associated teams and services
            escalation_policies = EscalationPolicy.query.all()
            data = []
            for policy in escalation_policies:
                # Handle cases where there may be no teams or no services
                teams = policy.teams if policy.teams else [None]
                services = policy.services if policy.services else [None]

                # Combine teams and services, making sure to include policies with missing relationships
                for team in teams:
                    for service in services:
                        data.append({
                            "escalation_policy_id": policy.id,
                            "escalation_policy_name": policy.name,
                            "team_id": team.id if team else None,
                            "team_name": team.name if team else "No Team",
                            "service_id": service.id if service else None,
                            "service_name": service.name if service else "No Service"
                        })
            fieldnames = ["escalation_policy_id", "escalation_policy_name",
                          "team_id", "team_name", "service_id", "service_name"]

        else:
            # If the id doesn't match, return 404
            abort(404, description="CSV type not found")

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in data:
            writer.writerow(row)

        csv_content = output.getvalue()
        response = Response(csv_content, mimetype='text/csv')
        response.headers['Content-Disposition'] = f"attachment; filename=data.csv"

        return response

    except Exception as e:
        # Catch and log any exception
        return jsonify({"error": "An error occurred while generating CSV", "details": str(e)}), 500


@app.route("/data")
def data():
    """
    API endpoint to get detailed information about the service with the most incidents,
    including incident breakdown by status.
    """
    try:
        # Query for the service with the most incidents
        service_most_incidents = db.session.query(
            Service,
            func.count(Incident.id).label('incident_count')
        ).join(Incident).group_by(Service.id).order_by(func.count(Incident.id).desc()).first()

        # If no service has incidents, return a message
        if service_most_incidents is None:
            return jsonify({"message": "No services have incidents"}), 404

        service, incident_count = service_most_incidents
        incidents = Incident.query.filter_by(service_id=service.id).all()

        incident_status_breakdown = {}
        for incident in incidents:
            status = incident.status
            if status not in incident_status_breakdown:
                incident_status_breakdown[status] = []
            incident_status_breakdown[status].append({
                "incident_id": incident.id,
                "incident_title": incident.title,
                "incident_description": incident.description,
                "incident_status": incident.status,
                "incident_url": incident.url
            })

        response_data = {
            "service_id": service.id,
            "service_name": service.name,
            "service_description": service.description,
            "service_url": service.url,
            "total_incidents": incident_count,
            "incident_status_breakdown": incident_status_breakdown
        }

        return jsonify(response_data), 200

    except Exception as e:
        # Catch and log any exception
        return jsonify({"error": "An error occurred", "details": str(e)}), 500


if __name__ == "__main__":
    with app.app_context():
        start_app()

    # Run the Flask app
    app.run(debug=True, port=5001, host="0.0.0.0")
