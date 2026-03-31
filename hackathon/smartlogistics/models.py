from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

Zone = Literal["A", "B", "C", "1", "2", "3"]
ActionType = Literal["move", "pickup", "deliver", "recharge", "wait"]
PackageStatus = Literal["pending", "picked", "delivered", "overdue"]

class PackageSpec(BaseModel):
    id: str
    origin: Zone
    destination: Zone
    priority: int = Field(ge=1, le=3)
    deadline: int = Field(ge=1)

class PackageState(PackageSpec):
    status: PackageStatus = "pending"
    carried: bool = False
    deadline_remaining: int = 0
    delivered_time: Optional[int] = None

    @field_validator("deadline_remaining", mode="before")
    def set_deadline_remaining(cls, v, info):
        if v is None:
            return info.data.get("deadline")
        return v

class PackageView(BaseModel):
    id: str
    origin: Zone
    destination: Zone
    priority: int
    deadline_remaining: int
    status: PackageStatus
    carried: bool

class Action(BaseModel):
    type: ActionType
    target_zone: Optional[Zone] = None
    package_id: Optional[str] = None

    @field_validator("target_zone", mode="before")
    def normalize_zone(cls, v):
        if v is None:
            return None
        return v

class Observation(BaseModel):
    time_step: int
    max_steps: int
    robot_location: Zone
    battery_level: int
    carrying: Optional[str]
    pending_packages: List[PackageView]
    delivered_packages: List[str]
    remaining_time: int
    total_reward: float

class EnvState(BaseModel):
    observation: Observation
    done: bool
    total_reward: float

class ScenarioConfig(BaseModel):
    name: str
    description: str
    max_steps: int = Field(gt=0)
    packages: List[PackageSpec]
    start_location: Zone = "A"
    initial_battery: int = Field(gt=0, le=100)

class TaskDefinition(BaseModel):
    id: str
    name: str
    description: str
    scenario: ScenarioConfig
    grader: str
