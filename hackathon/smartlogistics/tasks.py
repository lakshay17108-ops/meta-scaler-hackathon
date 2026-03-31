from .models import ScenarioConfig, PackageSpec, TaskDefinition

TASKS = [
    TaskDefinition(
        id="easy",
        name="easy_delivery",
        description="Deliver three packages across two zones within a relaxed time budget.",
        grader="easy",
        scenario=ScenarioConfig(
            name="easy_delivery",
            description="Simple delivery workflow with three packages and slack deadlines.",
            max_steps=12,
            initial_battery=100,
            packages=[
                PackageSpec(id="P1", origin="A", destination="1", priority=1, deadline=9),
                PackageSpec(id="P2", origin="B", destination="2", priority=1, deadline=10),
                PackageSpec(id="P3", origin="C", destination="3", priority=2, deadline=10),
            ],
        ),
    ),
    TaskDefinition(
        id="medium",
        name="medium_deadline",
        description="Five package deliveries with deadlines and mixed priorities.",
        grader="medium",
        scenario=ScenarioConfig(
            name="medium_deadline",
            description="Manage five packages with moderate deadlines and priority routing.",
            max_steps=16,
            initial_battery=100,
            packages=[
                PackageSpec(id="P1", origin="A", destination="2", priority=2, deadline=8),
                PackageSpec(id="P2", origin="B", destination="3", priority=3, deadline=9),
                PackageSpec(id="P3", origin="C", destination="1", priority=1, deadline=10),
                PackageSpec(id="P4", origin="B", destination="1", priority=2, deadline=11),
                PackageSpec(id="P5", origin="A", destination="3", priority=1, deadline=12),
            ],
        ),
    ),
    TaskDefinition(
        id="hard",
        name="hard_priority",
        description="Seven packages with tight deadlines, priority delivery, and battery management.",
        grader="hard",
        scenario=ScenarioConfig(
            name="hard_priority",
            description="Seven-package route planning with battery and deadline pressure.",
            max_steps=20,
            initial_battery=80,
            packages=[
                PackageSpec(id="P1", origin="A", destination="3", priority=3, deadline=8),
                PackageSpec(id="P2", origin="C", destination="2", priority=2, deadline=7),
                PackageSpec(id="P3", origin="B", destination="1", priority=3, deadline=9),
                PackageSpec(id="P4", origin="A", destination="2", priority=1, deadline=10),
                PackageSpec(id="P5", origin="C", destination="1", priority=2, deadline=11),
                PackageSpec(id="P6", origin="B", destination="3", priority=1, deadline=12),
                PackageSpec(id="P7", origin="A", destination="1", priority=3, deadline=9),
            ],
        ),
    ),
]

TASK_MAP = {task.id: task for task in TASKS}

def get_task_by_id(task_id: str) -> TaskDefinition:
    return TASK_MAP[task_id]
