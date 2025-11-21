from datetime import datetime
from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_current_user, require_admin, User
from .schemas import (
    CreateIncidentRequest,
    CreateRuleRequest,
    Incident,
    Rule,
    StatusResponse,
    TimelineEvent,
    TokenRequest,
    TokenResponse,
)
from .storage import seed_incidents, seed_rules, seed_statuses, seed_timeline

app = FastAPI(title="Monitoring Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

statuses: List[StatusResponse] = seed_statuses()
timeline: List[TimelineEvent] = seed_timeline()
incidents: Dict[str, Incident] = seed_incidents()
rules: Dict[str, Rule] = seed_rules()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(event)
            except WebSocketDisconnect:
                self.disconnect(connection)


manager = ConnectionManager()


async def _broadcast_event(event: TimelineEvent):
    event_payload = event.dict()
    await manager.broadcast(event_payload)


@app.post("/auth/token", response_model=TokenResponse)
async def issue_token(payload: TokenRequest):
    # This is a placeholder implementation. In production you would delegate to your OAuth2/SSO IdP.
    if payload.username == "admin" and payload.password:
        return TokenResponse(access_token="admin-token", role="admin")
    if payload.username and payload.password:
        return TokenResponse(access_token="viewer-token", role="viewer")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@app.get("/status", response_model=List[StatusResponse])
async def get_status(_: User = Depends(get_current_user)):
    return statuses


@app.get("/timeline", response_model=List[TimelineEvent])
async def get_timeline(_: User = Depends(get_current_user)):
    return sorted(timeline, key=lambda e: e.timestamp, reverse=True)


@app.get("/incidents", response_model=List[Incident])
async def get_incidents(_: User = Depends(get_current_user)):
    return list(incidents.values())


@app.post("/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(payload: CreateIncidentRequest, user: User = Depends(require_admin)):
    incident_id = f"inc-{len(incidents) + 1}"
    new_incident = Incident(
        id=incident_id,
        service=payload.service,
        summary=payload.summary,
        impact=payload.impact,
        opened_at=datetime.utcnow(),
        owner=payload.owner or user.username,
    )
    incidents[incident_id] = new_incident

    event = TimelineEvent(
        id=f"evt-{len(timeline) + 1}",
        service=payload.service,
        level="critical",
        message=f"Incident created: {payload.summary}",
        timestamp=datetime.utcnow(),
    )
    timeline.append(event)
    await _broadcast_event(event)
    return new_incident


@app.patch("/incidents/{incident_id}/close", response_model=Incident)
async def close_incident(incident_id: str, user: User = Depends(require_admin)):
    incident = incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    incident.closed_at = datetime.utcnow()
    event = TimelineEvent(
        id=f"evt-{len(timeline) + 1}",
        service=incident.service,
        level="info",
        message=f"Incident {incident_id} closed by {user.username}",
        timestamp=datetime.utcnow(),
    )
    timeline.append(event)
    await _broadcast_event(event)
    return incident


@app.get("/rules", response_model=List[Rule])
async def list_rules(_: User = Depends(get_current_user)):
    return list(rules.values())


@app.post("/rules", response_model=Rule, status_code=status.HTTP_201_CREATED)
async def create_rule(payload: CreateRuleRequest, _: User = Depends(require_admin)):
    rule_id = f"rule-{len(rules) + 1}"
    rule = Rule(id=rule_id, **payload.dict())
    rules[rule_id] = rule
    return rule


@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
