def generate_mock_plan(user_input):
    return {
        "meal_plan": f"""
Day 1:
- Breakfast: Oats + Yogurt
- Lunch: Chicken Rice Bowl
- Dinner: Grilled Veggies + Paneer

Day 2:
- Breakfast: Smoothie
- Lunch: Lentil Curry + Rice
- Dinner: Stir-fry Chicken
        """,

        "grocery_list": """
- Rice (500g)
- Chicken (400g)
- Yogurt (300g)
- Lentils (200g)
- Vegetables (mixed)
        """,

        "cooking_plan": """
Day -1:
- Marinate chicken overnight

Day 1:
- Preheat oven to 180°C
- Cook rice (15 min)
- Grill chicken (20 min)

Alternative:
- Air fryer: 170°C for 15 min
- Pan: medium heat 12 min
        """
    }