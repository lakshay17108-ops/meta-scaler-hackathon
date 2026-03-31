from __future__ import annotations
import copy
from typing import Dict, List, Optional
from .models import (
    Action,
    Observation,
    EnvState,
    PackageState,
    PackageView,
    ScenarioConfig,
)

VALID_ZONES = ["A", "B", "C", "1", "2", "3"]

class LogisticsEnv:
    def __init__(self, scenario: ScenarioConfig):
        self.scenario = scenario
        self.reset(scenario)

    def reset(self, scenario: Optional[ScenarioConfig] = None) -> Observation:
        if scenario is not None:
            self.scenario = scenario
        self.time_step = 0
        self.total_reward = 0.0
        self.robot_location = self.scenario.start_location
        self.battery_level = self.scenario.initial_battery
        self.carrying: Optional[str] = None
        self.done = False
        self.package_states: List[PackageState] = []

        for package in self.scenario.packages:
            self.package_states.append(
                PackageState(
                    **package.model_dump(),
                    status="pending",
                    carried=False,
                    deadline_remaining=package.deadline,
                )
            )

        return self.state().observation

    def state(self) -> EnvState:
        return EnvState(
            observation=self._build_observation(),
            done=self.done,
            total_reward=round(self.total_reward, 4),
        )

    def step(self, action: Action) -> EnvState:
        if self.done:
            return self.state()

        self.time_step += 1
        reward = 0.0

        if self.battery_level <= 0:
            self.done = True
            return self._finalize_state(reward)

        if action.type == "move":
            reward += self._move(action)
        elif action.type == "pickup":
            reward += self._pickup(action)
        elif action.type == "deliver":
            reward += self._deliver(action)
        elif action.type == "recharge":
            reward += self._recharge(action)
        elif action.type == "wait":
            reward -= 0.05
        else:
            reward -= 0.2

        reward += self._update_deadlines()
        if self.battery_level <= 0:
            self.battery_level = 0
            reward -= 0.5

        self.total_reward += reward
        self.total_reward = round(self.total_reward, 6)

        self.done = self._check_done()
        return self._finalize_state(reward)

    def _move(self, action: Action) -> float:
        if not action.target_zone or action.target_zone not in VALID_ZONES:
            return -0.3
        if action.target_zone == self.robot_location:
            self.battery_level = max(0, self.battery_level - 1)
            return -0.05

        self.robot_location = action.target_zone
        self.battery_level = max(0, self.battery_level - 10)
        return 0.0

    def _pickup(self, action: Action) -> float:
        if self.carrying is not None:
            return -0.2
        package = self._find_package(action.package_id)
        if not package or package.origin != self.robot_location or package.status not in {"pending", "overdue"}:
            return -0.4
        package.carried = True
        package.status = "picked"
        self.carrying = package.id
        self.battery_level = max(0, self.battery_level - 5)
        return 0.2 + 0.05 * package.priority

    def _deliver(self, action: Action) -> float:
        if self.carrying is None or self.carrying != action.package_id:
            return -0.4
        package = self._find_package(action.package_id)
        if not package or package.destination != self.robot_location:
            return -0.4
        package.carried = False
        package.status = "delivered"
        package.delivered_time = self.time_step
        self.carrying = None
        self.battery_level = max(0, self.battery_level - 5)
        reward = 1.0 + 0.1 * package.priority
        if package.deadline_remaining >= 0:
            reward += 0.3
        else:
            reward -= 0.3
        return reward

    def _recharge(self, action: Action) -> float:
        if self.robot_location != "A":
            return -0.3
        if self.battery_level >= 100:
            return -0.1
        self.battery_level = 100
        return 0.05

    def _update_deadlines(self) -> float:
        reward = 0.0
        for package in self.package_states:
            if package.status == "pending":
                package.deadline_remaining -= 1
                if package.deadline_remaining < 0:
                    package.status = "overdue"
                    reward -= 0.35
        return reward

    def _check_done(self) -> bool:
        if self.time_step >= self.scenario.max_steps:
            return True
        if self.battery_level <= 0:
            return True
        if all(pkg.status == "delivered" for pkg in self.package_states):
            return True
        return False

    def _finalize_state(self, reward: float) -> EnvState:
        return self.state()

    def _build_observation(self) -> Observation:
        pending_packages = [
            PackageView(
                id=pkg.id,
                origin=pkg.origin,
                destination=pkg.destination,
                priority=pkg.priority,
                deadline_remaining=pkg.deadline_remaining,
                status=pkg.status,
                carried=pkg.carried,
            )
            for pkg in self.package_states
        ]
        delivered_packages = [pkg.id for pkg in self.package_states if pkg.status == "delivered"]
        return Observation(
            time_step=self.time_step,
            max_steps=self.scenario.max_steps,
            robot_location=self.robot_location,
            battery_level=self.battery_level,
            carrying=self.carrying,
            pending_packages=pending_packages,
            delivered_packages=delivered_packages,
            remaining_time=max(0, self.scenario.max_steps - self.time_step),
            total_reward=self.total_reward,
        )

    def _find_package(self, package_id: Optional[str]) -> Optional[PackageState]:
        if not package_id:
            return None
        for package in self.package_states:
            if package.id == package_id:
                return package
        return None
