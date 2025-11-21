from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Notification:
    host: str
    service: str
    state: str
    severity: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    def key(self) -> str:
        host_part = self.host.replace(" ", "_").lower()
        service_part = self.service.replace(" ", "_").lower()
        state_part = self.state.replace(" ", "_").lower()
        return f"{host_part}:{service_part}:{state_part}"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "service": self.service,
            "state": self.state,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }
