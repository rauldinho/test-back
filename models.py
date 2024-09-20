from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

service_team = db.Table("service_team",
                        db.Column("service_id", db.String(20), db.ForeignKey(
                            "service.id"), primary_key=True),
                        db.Column("team_id", db.String(20), db.ForeignKey(
                            "team.id"), primary_key=True),

                        )

escalation_policy_team = db.Table("escalation_policy_team",
                                  db.Column("escalation_policy_id", db.String(20), db.ForeignKey(
                                      "escalation_policy.id"), primary_key=True),
                                  db.Column("team_id", db.String(20), db.ForeignKey("team.id"), primary_key=True))


class Team(db.Model):
    id = db.Column(db.String(20), nullable=False, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    url = db.Column(db.String(100), nullable=False, default="#")

    def __repr__(self):
        return f"<Team {self.id}: {self.name}>"


class EscalationPolicy(db.Model):

    id = db.Column(db.String(20), nullable=False, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    url = db.Column(db.String(100), nullable=False, default="#")
    # Relationships
    services = db.relationship(
        "Service", backref="escalation_policy", lazy=True)
    incidents = db.relationship(
        "Incident", backref="escalation_policy", lazy=True)
    teams = db.relationship("Team", secondary=escalation_policy_team,
                            backref=db.backref("escalation_policies", lazy=True))

    def __repr__(self):
        return f"<EscalationPolicy {self.id}: {self.name}>"


class Service(db.Model):
    id = db.Column(db.String(20), nullable=False, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(250), nullable=False, default="N/A")
    status = db.Column(db.String(10), nullable=False, default="N/A")
    url = db.Column(db.String(100), nullable=False, default="#")
    # Relationships
    incidents = db.relationship("Incident", backref="service", lazy=True)
    escalation_policy_id = db.Column(
        db.String(20), db.ForeignKey("escalation_policy.id"))
    teams = db.relationship("Team", secondary=service_team,
                            backref=db.backref("services", lazy=True))

    def __repr__(self):
        return f"<Service {self.id}: {self.name}>"


class Incident(db.Model):
    id = db.Column(db.String(20), nullable=False, primary_key=True)
    title = db.Column(db.String(50), nullable=False, default="N/A")
    description = db.Column(db.String(100), nullable=False, default="N/A")
    status = db.Column(db.String(10), nullable=False, default="N/A")
    url = db.Column(db.String(100), nullable=False, default="#")
    # Relationships
    service_id = db.Column(db.String(20), db.ForeignKey("service.id"))
    escalation_policy_id = db.Column(
        db.String(20), db.ForeignKey("escalation_policy.id"))

    def __repr__(self):
        return f"<Incident {self.id}: {self.title}>"
