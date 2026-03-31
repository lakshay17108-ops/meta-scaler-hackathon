from typing import Dict
from .models import TaskDefinition

GRADER_MAP: Dict[str, str] = {
    "easy": "easy",
    "medium": "medium",
    "hard": "hard",
}


def grade_environment(env, grader_name: str) -> float:
    total = len(env.package_states)
    if total == 0:
        return 0.0

    delivered = sum(1 for p in env.package_states if p.status == "delivered")
    on_time = sum(
        1
        for p in env.package_states
        if p.status == "delivered" and p.delivered_time is not None and p.delivered_time <= p.deadline
    )
    delivered_ratio = delivered / total
    on_time_ratio = on_time / total
    efficiency = max(0.0, 1.0 - env.time_step / env.scenario.max_steps)
    battery_factor = env.battery_level / 100.0

    if grader_name == "easy":
        score = delivered_ratio
    elif grader_name == "medium":
        score = 0.5 * delivered_ratio + 0.3 * on_time_ratio + 0.2 * efficiency
    else:
        score = 0.4 * delivered_ratio + 0.3 * on_time_ratio + 0.2 * efficiency + 0.1 * battery_factor

    return max(0.0, min(1.0, round(score, 4)))
