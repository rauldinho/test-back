CREATE TABLE team (
        id VARCHAR(20) NOT NULL,
        name VARCHAR(20) NOT NULL,
        url VARCHAR(100) NOT NULL,
        PRIMARY KEY (id)
);
CREATE TABLE escalation_policy (
        id VARCHAR(20) NOT NULL,
        name VARCHAR(20) NOT NULL,
        url VARCHAR(100) NOT NULL,
        PRIMARY KEY (id)
);
CREATE TABLE escalation_policy_team (
        escalation_policy_id VARCHAR(20) NOT NULL,
        team_id VARCHAR(20) NOT NULL,
        PRIMARY KEY (escalation_policy_id, team_id),
        FOREIGN KEY(escalation_policy_id) REFERENCES escalation_policy (id),
        FOREIGN KEY(team_id) REFERENCES team (id)
);
CREATE TABLE service (
        id VARCHAR(20) NOT NULL,
        name VARCHAR(10) NOT NULL,
        description VARCHAR(10) NOT NULL,
        status VARCHAR(10) NOT NULL,
        url VARCHAR(100) NOT NULL,
        escalation_policy_id VARCHAR(20),
        PRIMARY KEY (id),
        FOREIGN KEY(escalation_policy_id) REFERENCES escalation_policy (id)
);
CREATE TABLE service_team (
        service_id VARCHAR(20) NOT NULL,
        team_id VARCHAR(20) NOT NULL,
        PRIMARY KEY (service_id, team_id),
        FOREIGN KEY(service_id) REFERENCES service (id),      
        FOREIGN KEY(team_id) REFERENCES team (id)
);
CREATE TABLE incident (
        id VARCHAR(20) NOT NULL,
        title VARCHAR(50) NOT NULL,
        description VARCHAR(100) NOT NULL,
        status VARCHAR(10) NOT NULL,
        url VARCHAR(100) NOT NULL,
        service_id VARCHAR(20),
        escalation_policy_id VARCHAR(20),
        PRIMARY KEY (id),
        FOREIGN KEY(service_id) REFERENCES service (id),      
        FOREIGN KEY(escalation_policy_id) REFERENCES escalation_policy (id)
);