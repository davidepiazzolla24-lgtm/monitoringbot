from datetime import datetime, timedelta
from typing import Dict, List

from .schemas import Incident, Rule, ServiceStatus, StatusResponse, TimelineEvent


def seed_statuses() -> List[StatusResponse]:
    now = datetime.utcnow()
    return [
        StatusResponse(service="api", status=ServiceStatus.healthy, updated_at=now, details="Operational"),
        StatusResponse(service="worker", status=ServiceStatus.degraded, updated_at=now - timedelta(minutes=3), details="Retrying queue saturation"),
        StatusResponse(service="db", status=ServiceStatus.healthy, updated_at=now - timedelta(minutes=1)),
    ]


def seed_timeline() -> List[TimelineEvent]:
    now = datetime.utcnow()
    return [
        TimelineEvent(id="evt-1", service="worker", level="warning", message="Queue depth exceeded threshold", timestamp=now - timedelta(minutes=10)),
        TimelineEvent(id="evt-2", service="api", level="info", message="Deployment completed", timestamp=now - timedelta(minutes=30)),
        TimelineEvent(id="evt-3", service="db", level="info", message="Backup finished", timestamp=now - timedelta(hours=1)),
    ]


def seed_incidents() -> Dict[str, Incident]:
    now = datetime.utcnow()
    return {
        "inc-1": Incident(
            id="inc-1",
            service="worker",
            summary="Slow queue consumption",
            impact="delayed processing",
            opened_at=now - timedelta(hours=2),
            owner="oncall@company.test",
        )
    }


def seed_rules() -> Dict[str, Rule]:
    return {
        "rule-1": Rule(
            id="rule-1",
            name="High worker latency",
            expression="latency_p95 > 2s",
            severity="critical",
            description="Triggers when worker p95 latency exceeds 2s for 5m",
            enabled=True,
        ),
        "rule-2": Rule(
            id="rule-2",
            name="Queue depth",
            expression="queue_depth > 5000",
            severity="warning",
            description="Alerts when queues accumulate too many pending jobs",
            enabled=True,
        ),
    }
