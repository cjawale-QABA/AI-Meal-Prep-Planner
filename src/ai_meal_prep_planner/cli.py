import click
from .planner import generate_meal_plan


@click.command()
@click.option("--days", default=3, help="Number of days to plan for.")
def main(days):
    """Simple CLI for the AI Meal Prep Planner."""
    plan = generate_meal_plan(days)
    click.echo("Generated meal plan:")
    for day, meals in enumerate(plan, start=1):
        click.echo(f"Day {day}: {', '.join(meals)}")


if __name__ == "__main__":
    main()
