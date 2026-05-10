from dataclasses import dataclass, field
from typing import List, Optional
import json
import os
import time


@dataclass
class AgentTrustProfile:
    agent_id: str
    session_count: int = 0
    total_ddcs: int = 0
    risk_classes_used: List[str] = field(default_factory=list)
    highest_risk_authorized: str = "read_only"
    trust_score: float = 0.5
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    last_seen: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def record_session(self):
        self.session_count += 1
        self.last_seen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def record_ddc(self, risk_class: str):
        self.total_ddcs += 1
        if risk_class not in self.risk_classes_used:
            self.risk_classes_used.append(risk_class)


class LocalATP:
    """Local Agent Trust Profile — disk-only, ephemeral.

    Tracks agent behavior across sessions for local trust scoring.
    Upgradable to cloud ATP when using RelayToolTrustClient.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.expanduser("~/.ardyn/atp/")
        os.makedirs(self.storage_path, exist_ok=True)

    def _file_path(self, agent_id: str) -> str:
        return os.path.join(self.storage_path, f"{agent_id}.json")

    def get(self, agent_id: str) -> AgentTrustProfile:
        path = self._file_path(agent_id)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            return AgentTrustProfile(**data)
        profile = AgentTrustProfile(agent_id=agent_id)
        self.save(profile)
        return profile

    def save(self, profile: AgentTrustProfile) -> None:
        path = self._file_path(profile.agent_id)
        data = {
            "agent_id": profile.agent_id,
            "session_count": profile.session_count,
            "total_ddcs": profile.total_ddcs,
            "risk_classes_used": profile.risk_classes_used,
            "highest_risk_authorized": profile.highest_risk_authorized,
            "trust_score": profile.trust_score,
            "created_at": profile.created_at,
            "last_seen": profile.last_seen,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def list_agents(self) -> List[str]:
        return [
            f.replace(".json", "")
            for f in os.listdir(self.storage_path)
            if f.endswith(".json")
        ]