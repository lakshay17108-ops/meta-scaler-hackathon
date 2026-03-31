import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from smartlogistics import TASKS
from smartlogistics.environment import LogisticsEnv
from smartlogistics.grader import grade_environment
from smartlogistics.models import Action


def load_llm_client():
    api_base = os.getenv("API_BASE_URL")
    api_key = os.getenv("HF_TOKEN")
    model_name = os.getenv("MODEL_NAME")
    if not api_base or not api_key or not model_name:
        return None, None
    return OpenAI(api_key=api_key, base_url=api_base), model_name


def safe_text(output: Any) -> str:
    if isinstance(output, str):
        return output
    if isinstance(output, dict):
        return output.get("text", "")
    if isinstance(output, list):
        return "".join(safe_text(item) for item in output)
    return str(output)


def parse_response_text(response) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text
    output = getattr(response, "output", None)
    if output is None:
        return ""
    if isinstance(output, list):
        return safe_text(output)
    if isinstance(output, dict):
        return safe_text(output.get("content", {}))
    return str(output)


def parse_actions(text: str) -> List[Action]:
    try:
        payload = json.loads(text)
        if isinstance(payload, dict) and "actions" in payload:
            payload = payload["actions"]
        actions = [Action(**item) for item in payload]
        return actions
    except Exception:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        actions: List[Action] = []
        for line in lines:
            if line.startswith("[") or line.startswith("{"):
                continue
            parts = [segment.strip() for segment in line.replace("{", "").replace("}", "").split(",")]
            data: Dict[str, Any] = {}
            for part in parts:
                if ":" not in part:
                    continue
                key, value = part.split(":", 1)
                data[key.strip().strip('"')] = value.strip().strip('"')
            if data:
                actions.append(Action(**data))
        return actions


def prompt_for_task(task) -> str:
    initial_state = LogisticsEnv(task.scenario).reset().model_dump()
    return (
        f"You are controlling a warehouse delivery robot in a logistics environment. "
        f"The task is: {task.description}\n\n"
        f"Initial observation:\n{json.dumps(initial_state, indent=2)}\n\n"
        "Action schema:\n"
        "- type: move, pickup, deliver, recharge, wait\n"
        "- move requires target_zone\n"
        "- pickup and deliver require package_id\n"
        "Return a JSON array of actions only, for example:\n"
        "[{\"type\": \"move\", \"target_zone\": \"B\"}, {\"type\": \"pickup\", \"package_id\": \"P1\"}]"
    )


def llm_plan(client: OpenAI, model_name: str, task) -> List[Action]:
    prompt = prompt_for_task(task)
    response = client.responses.create(model=model_name, input=prompt, temperature=0, max_tokens=400)
    text = parse_response_text(response)
    actions = parse_actions(text)
    if not actions:
        raise ValueError("No valid actions parsed from LLM response")
    return actions


def heuristic_plan(task) -> List[Action]:
    env = LogisticsEnv(task.scenario)
    env.reset()
    plan: List[Action] = []

    def nearest_pending_package():
        pending = [p for p in env.package_states if p.status == "pending"]
        if not pending:
            return None
        return min(pending, key=lambda p: (p.deadline_remaining, p.priority))

    while not env.done:
        if env.carrying:
            package = next((p for p in env.package_states if p.id == env.carrying), None)
            if package is None:
                break
            if env.robot_location == package.destination:
                action = Action(type="deliver", package_id=package.id)
            else:
                action = Action(type="move", target_zone=package.destination)
        else:
            package = nearest_pending_package()
            if package is None:
                action = Action(type="wait")
            elif env.robot_location == package.origin:
                action = Action(type="pickup", package_id=package.id)
            else:
                action = Action(type="move", target_zone=package.origin)
        plan.append(action)
        env.step(action)
        if len(plan) >= env.scenario.max_steps:
            break
    return plan


def run_task(task, client: Optional[OpenAI], model_name: Optional[str]) -> None:
    print(f"\n=== Task {task.id}: {task.name} ===")
    env = LogisticsEnv(task.scenario)
    env.reset()

    if client and model_name:
        try:
            actions = llm_plan(client, model_name, task)
            print(f"LLM plan loaded ({len(actions)} actions)")
        except Exception as exc:
            print(f"LLM planning failed: {exc}. Falling back to heuristic baseline.")
            actions = heuristic_plan(task)
    else:
        print("OpenAI variables not configured. Using heuristic baseline.")
        actions = heuristic_plan(task)

    env.reset()
    for action in actions:
        if env.done:
            break
        try:
            env.step(action)
        except Exception as exc:
            print(f"Invalid action {action}: {exc}")
            break
    score = grade_environment(env, task.grader)
    print(f"Score: {score:.4f} | Total reward: {env.total_reward:.4f} | Delivered: {sum(1 for p in env.package_states if p.status == 'delivered')}/{len(env.package_states)} | Steps: {env.time_step}")


def main():
    client, model_name = load_llm_client()
    print("Smart Logistics baseline inference")
    if client:
        print("OpenAI client configured.")
    else:
        print("OpenAI variables missing. Running deterministic fallback.")

    for task in TASKS:
        run_task(task, client, model_name)


if __name__ == "__main__":
    main()
