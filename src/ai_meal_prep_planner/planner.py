from typing import List


def generate_meal_plan(days: int) -> List[List[str]]:
    """Generate a simple deterministic meal plan for `days` days.

    This is a small placeholder function to make the repository a runnable Python
    project. It returns 3 meals per day.
    """
    if days <= 0:
        return []

    base_meals = ["Oatmeal", "Salad", "Grilled Chicken"]
    plan = []
    for i in range(days):
        # rotate meals to produce variation
        rotated = base_meals[i % len(base_meals):] + base_meals[: i % len(base_meals)]
        plan.append(rotated)
    return plan
