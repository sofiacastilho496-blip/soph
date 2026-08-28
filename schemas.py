from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EventSchema(BaseModel):
    type: str = Field(..., description="Tipo do evento (ex: state_change, collision)")
    target_id: Optional[str] = None
    property: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

class EntityObservationSchema(BaseModel):
    id: str
    distance_studs: float
    is_moving: bool

class ObjectObservationSchema(BaseModel):
    id: str
    shape: str
    material: str
    distance_studs: float

class ObservationFrameSchema(BaseModel):
    protocol_version: str = Field(..., pattern=r"^0\.2$")
    agent_id: str
    server_id: str
    frame_id: str
    timestamp: float
    entities: List[EntityObservationSchema] = []
    objects: List[ObjectObservationSchema] = []
    events: List[EventSchema] = []

class ExpectedEffectSchema(BaseModel):
    target_id: Optional[str] = None
    state: Optional[str] = None
    timeout_seconds: float = 3.0

class ActionProposalSchema(BaseModel):
    protocol_version: str = "0.2"
    request_id: str
    intent: str
    target_id: Optional[str] = None
    parameters: Dict[str, Any] = {}
    expected_effect: ExpectedEffectSchema