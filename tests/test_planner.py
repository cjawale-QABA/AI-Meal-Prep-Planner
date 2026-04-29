from ai_meal_prep_planner.planner import generate_meal_plan


def test_generate_meal_plan_basic():
    plan = generate_meal_plan(2)
    assert len(plan) == 2
    assert all(len(day) == 3 for day in plan)


def test_generate_meal_plan_zero():
    assert generate_meal_plan(0) == []
