import asyncio
import aiohttp
import os
from models import db, Service, Team, Incident, EscalationPolicy
from dotenv import load_dotenv
from abc import ABC, abstractmethod

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


class PagerDutyAPIService:
    """Service class responsible for fetching data from PagerDuty API."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def fetch_data(self, name, url):
        """
        Fetch paginated data from the given PagerDuty API endpoint.
        """
        all_data = []
        offset = 0
        while True:
            params = {"offset": offset}
            async with self.session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()  # Ensure a valid response
                data = await response.json()
                all_data.extend(data[name])

                if not data["more"]:
                    break
                offset += data["limit"]
        return all_data


class Repository(ABC):
    """Abstract base class for repositories."""

    @abstractmethod
    def store(self, data):
        pass


class ServiceRepository(Repository):
    def store(self, services):
        for service in services:
            escalation_policy_id = service.get(
                "escalation_policy", {}).get("id")
            service_obj = Service(
                id=service["id"],
                name=service.get("name", "N/A"),
                description=service.get("description", "N/A"),
                status=service.get("status", "N/A"),
                url=service.get("html_url", "#"),
                escalation_policy_id=escalation_policy_id
            )
            db.session.add(service_obj)

            for team in service.get("teams", []):
                team_obj = Team.query.get(team["id"])
                if team_obj:
                    service_obj.teams.append(team_obj)
            db.session.merge(service_obj)
        db.session.commit()


class IncidentRepository(Repository):
    def store(self, incidents):
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
            db.session.merge(incident_obj)
        db.session.commit()


class TeamRepository(Repository):
    def store(self, teams):
        for team in teams:
            team_obj = Team(
                id=team["id"],
                name=team.get("name", "N/A"),
                url=team.get("html_url", "#")
            )
            db.session.merge(team_obj)
        db.session.commit()


class EscalationPolicyRepository(Repository):
    def store(self, policies):
        for policy in policies:
            policy_obj = EscalationPolicy(
                id=policy["id"],
                name=policy.get("name", "N/A"),
                url=policy.get("html_url", "#")
            )
            db.session.add(policy_obj)
            for team in policy.get("teams", []):
                team_obj = Team.query.get(team["id"])
                if team_obj:
                    policy_obj.teams.append(team_obj)
            db.session.merge(policy_obj)
        db.session.commit()


class DataManager:
    """High-level manager responsible for coordinating fetching and storing of data."""

    def __init__(self, api_service, repositories):
        self.api_service = api_service
        self.repositories = repositories

    async def fetch_and_store(self):
        data = await asyncio.gather(
            self.api_service.fetch_data(
                "services", f"{PAGERDUTY_API_URL}/services"),
            self.api_service.fetch_data(
                "incidents", f"{PAGERDUTY_API_URL}/incidents"),
            self.api_service.fetch_data("teams", f"{PAGERDUTY_API_URL}/teams"),
            self.api_service.fetch_data("escalation_policies", f"{
                                        PAGERDUTY_API_URL}/escalation_policies")
        )

        result = {
            "services": data[0],
            "incidents": data[1],
            "teams": data[2],
            "escalation_policies": data[3]
        }

        self.repositories['teams'].store(result["teams"])
        self.repositories['escalation_policies'].store(
            result["escalation_policies"])
        self.repositories['services'].store(result["services"])
        self.repositories['incidents'].store(result["incidents"])


async def main():
    async with aiohttp.ClientSession() as session:
        api_service = PagerDutyAPIService(session)
        repositories = {
            "services": ServiceRepository(),
            "incidents": IncidentRepository(),
            "teams": TeamRepository(),
            "escalation_policies": EscalationPolicyRepository()
        }
        data_manager = DataManager(api_service, repositories)
        await data_manager.fetch_and_store()
