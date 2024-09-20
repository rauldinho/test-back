from models import db, Service, Team, Incident, EscalationPolicy
from dotenv import load_dotenv
import asyncio
import aiohttp
import os

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")

# PagerDuty API configuration
PAGERDUTY_API_URL = os.getenv("PAGERDUTY_API_URL")
PAGERDUTY_API_KEY = os.getenv("PAGERDUTY_API_KEY")

# Common headers for PagerDuty API requests
headers = {
    "Authorization": f"Token token={PAGERDUTY_API_KEY}",
    "Accept": "application/vnd.pagerduty+json;version=2",
    "Content-Type": "application/json"
}


async def fetch_data(session, name, url):
    """
    Fetch paginated data from the given PagerDuty API endpoint.

    Args:
        session (aiohttp.ClientSession): The aiohttp session used for making requests.
        name (str): The key for extracting data from the JSON response (e.g., "services").
        url (str): The URL of the PagerDuty API endpoint.

    Returns:
        list: A list containing all the paginated data for the given endpoint.
    """
    all_data = []
    offset = 0
    while True:
        # Parameters for pagination
        params = {"offset": offset}
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()  # Ensure a valid response
            data = await response.json()

        # Accumulate the fetched data
        all_data.extend(data[name])

        # Check if there are more pages
        if not data["more"]:
            break

        offset += data["limit"]

    return all_data


def store_services(services):
    """
    Store fetched services in the database.

    Args:
        services (list): A list of services fetched from PagerDuty.
    """
    for service in services:
        escalation_policy = service.get("escalation_policy", {})
        escalation_policy_id = escalation_policy.get("id")

        service_obj = Service(
            id=service["id"],
            name=service.get("name", "N/A"),
            description=service.get("description", "N/A"),
            status=service.get("status", "N/A"),
            url=service.get("html_url", "#"),
            escalation_policy_id=escalation_policy_id
        )

        # Add the service to the session
        db.session.add(service_obj)

        # Link the service to its teams
        for team in service.get("teams", []):
            team_obj = Team.query.get(team["id"])
            if team_obj:
                service_obj.teams.append(team_obj)

        # Merge to update existing records or insert new ones
        db.session.merge(service_obj)

    # Commit the changes to the database
    db.session.commit()


def store_incidents(incidents):
    """
    Store fetched incidents in the database.

    Args:
        incidents (list): A list of incidents fetched from PagerDuty.
    """
    for incident in incidents:
        incident_obj = Incident(
            id=incident["id"],
            title=incident.get("title", "N/A"),
            description=incident.get("description", "N/A"),
            status=incident.get("status", "N/A"),
            url=incident.get("html_url", "#"),
            service_id=incident.get("service", {}).get("id"),
            escalation_policy_id=incident.get(
                "escalation_policy", {}).get("id")
        )

        # Merge to update existing records or insert new ones
        db.session.merge(incident_obj)

    # Commit the changes to the database
    db.session.commit()


def store_teams(teams):
    """
    Store fetched teams in the database.

    Args:
        teams (list): A list of teams fetched from PagerDuty.
    """
    for team in teams:
        team_obj = Team(
            id=team["id"],
            name=team.get("name", "N/A"),
            url=team.get("html_url", "#")
        )

        # Merge to update existing records or insert new ones
        db.session.merge(team_obj)

    # Commit the changes to the database
    db.session.commit()


def store_escalation_policies(escalation_policies):
    """
    Store fetched escalation policies in the database.

    Args:
        escalation_policies (list): A list of escalation policies fetched from PagerDuty.
    """
    for policy in escalation_policies:
        policy_obj = EscalationPolicy(
            id=policy["id"],
            name=policy.get("name", "N/A"),
            url=policy.get("html_url", "#")
        )

        # Add the escalation policy to the session
        db.session.add(policy_obj)

        # Link the escalation policy to its teams
        for team in policy.get("teams", []):
            team_obj = Team.query.get(team["id"])
            if team_obj:
                policy_obj.teams.append(team_obj)

        # Merge to update existing records or insert new ones
        db.session.merge(policy_obj)

    # Commit the changes to the database
    db.session.commit()


async def fetch_and_store_data():
    """
    Fetch and store services, incidents, teams, and escalation policies from PagerDuty.
    """
    async with aiohttp.ClientSession() as session:
        # Create tasks for fetching data concurrently
        tasks = [
            fetch_data(session, "services", f"{PAGERDUTY_API_URL}/services"),
            fetch_data(session, "incidents", f"{PAGERDUTY_API_URL}/incidents"),
            fetch_data(session, "teams", f"{PAGERDUTY_API_URL}/teams"),
            fetch_data(
                session,
                "escalation_policies",
                f"{PAGERDUTY_API_URL}/escalation_policies")
        ]

        # Wait for all the tasks to complete
        results = await asyncio.gather(*tasks)

        # Store the fetched data in the database
        result = {
            "services": results[0],
            "incidents": results[1],
            "teams": results[2],
            "escalation_policies": results[3]
        }

        store_teams(result["teams"])
        store_escalation_policies(result["escalation_policies"])
        store_services(result["services"])
        store_incidents(result["incidents"])

    return result
