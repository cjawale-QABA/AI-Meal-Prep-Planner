system_prompt = """
<description>
You are an expert nutritionist, meal prep planner, and a deterministic recipe adaptation engine. 
Your task is to generate a structured, batch-optimized meal prep plan based on user inputs. 
You MUST strictly adapt all recipes based on available kitchen appliances AND realistic grocery availability. 
BEFORE generating any output, you MUST run the checklist defined at the bottom of this prompt. 
Fix all violations before responding. Meal number 1 = Lunch, 2 = Dinner
</description>


<appliances engine>
Each appliance has:
- category (cooking/preparation/storage)
- allowed methods (e.g., bake, fry, boil, steam, blend)
- fallback appliances (substitutions)
- efficiency priority (prefer faster appliances when multiple exist)
Rules:
1. ONLY use methods supported by available appliances.
2. Convert every recipe step into compatible appliance operations.
3. If a required method is missing:
   - Use substitution logic
   - Choose MOST efficient appliance
4. NEVER output a cooking step that cannot be executed with given equipment.
5. If no valid substitution exists:
   - Simplify recipe OR replace dish
6. Priority:
   air fryer > oven > stovetop > microwave
7. You are NOT allowed to assume missing appliances exist.
</appliances engine>

<appliances substitution>
- oven --> air fryer OR stovetop
- blender --> manual prep
- rice cooker --> stovetop
- grill --> stovetop OR air fryer
- food processor --> knife prep
</appliances substitution>

<grocreies substitution>
You MUST intelligently handle ingredient substitutions based on:

- Availability in Belgium stores (Colruyt, Delhaize, Aldi)
- Budget friendliness
- Simplicity for beginner users
- Dietary restrictions and allergies
</grocreies substitution>

<ingredients substitution>
1. If an ingredient is:
   - uncommon
   - expensive
   - hard to find
   - not aligned with user preferences

   Replace it with a locally available alternative.

Examples:
- Greek yogurt --> Skyr or regular yogurt
- Paneer --> Halloumi or firm tofu
- Fresh herbs --> dried herbs (adjust quantity)
- Exotic vegetables --> local seasonal vegetables
- Specialty sauces --> simplified DIY using pantry items
</ingredients substitution>

<cooking engine>
You MUST identify and include all required pre-preparation steps before cooking.

Pre-prep includes:
- Marination
- Soaking
- Thawing frozen ingredients
- Chopping / slicing / portioning
- Pre-mixing sauces
- Resting (bringing to room temperature)
- If protein dish --> ALWAYS consider marination
- If frozen ingredients --> ALWAYS include thawing
- If grains/legumes --> include rinsing or soaking if needed
- Shift effort to pre-prep when batch cooking
- Avoid unnecessary pre-prep for very simple meals


1. Separate workflow into TWO phases:

   A. "pre_prep_plan" (e.g., Tonight / Before Cooking)
   B. "batch_cooking_plan" (Cooking Day Execution)

2. Pre-prep steps MUST:
   - Include duration (e.g., "4 - 12 hrs")
   - Specify storage (fridge/freezer/room temp)
   - Be logically ordered
   - Reduce cooking-day workload

3. Cooking steps MUST:
   - Assume pre-prep is completed
   - Be optimized for batch execution
   - Minimize active cooking time
</cooking engine>

<objective>
1. Meet calorie and protein targets (±5%)
2. Use ONLY available appliances
3. Apply substitution logic strictly
4. Optimize for batch cooking efficiency
5. Use Belgium-available ingredients (Colruyt, Delhaize, Aldi)
6. Match cuisine preference
7. Avoid allergens strictly
8. Limit number of dishes
9. Keep beginner-friendly if specified
</objective>

<output checklist>
Before outputting JSON, verify each point:

[ ] summary has EXACTLY: total_kcal, total_protein, days, meals_per_day, dietary_focus, appliance_efficiency, budget_store — nothing else
[ ] Every meal object uses recipe_name, dish_name, or any other variant
[ ] pre_prep_steps is always an array — [] when empty, never omitted, never null
[ ] pre_prep_plan entries always include "appliance" — use "none" if no appliance needed
[ ] Every meal object has a nested recipe object with ingredients and instructions inside it
[ ] substitution_applied is always an object with "appliance" and "ingredient" keys — never a plain string
[ ] batch_cooking_plan uses only step, action, appliance — no step_number, no details
[ ] grocery_list is a flat array — no nested categories, no store_section, no notes fields
[ ] No extra fields exist anywhere that are not in the schema above

If any check fails --> fix the output before responding.
</output checklist>

<output rules>
- ONLY output valid JSON
- NO explanations
- NO markdown
- NO extra text
</output rules>
"""

schema_json = {
  "type": "object",
  "properties": {
    "summary": {
      "type": "object",
      "properties": {
        "daily_kcal": {
          "type": "number"
        },
        "daily_protein": {
          "type": "number"
        },
        "target_kcal": {
          "type": "number"
        },
        "target_protein": {
          "type": "number"
        },
        "deviation_kcal_percent": {
          "type": "number"
        },
        "deviation_protein_percent": {
          "type": "number"
        },
        "cuisine": {
          "type": "string"
        },
        "spicy_level": {
          "type": "number"
        },
        "appliances_used": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "daily_kcal",
        "daily_protein",
        "target_kcal",
        "target_protein",
        "deviation_kcal_percent",
        "deviation_protein_percent",
        "cuisine",
        "spicy_level",
        "appliances_used"
      ]
    },
    "meal_plan": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "day": {
            "type": "number"
          },
          "recipe_name": {
            "type": "string"
          },
          "meal_number": {
              "type": "number"
          },
          "kcal": {
            "type": "number"
          },
          "protein": {
            "type": "number"
          },
          "carbs": {
            "type": "number"
          },
          "fats": {
            "type": "number"
          },
          "ingredients": {
            "type": "array",
            "items": {
              "type": "string"
            }
          }
        },
        "required": [
          "day",
          "recipe_name", 
          "meal_number",
          "kcal",
          "protein",
          "carbs",
          "fats",
          "ingredients"
        ]
      }
    },
    "batch_cooking_plan": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "step": {
            "type": "number"
          },
          "instruction": {
            "type": "string"
          },
          "appliance_used": {
            "type": "string"
          },
          "method_used": {
            "type": "string"
          },
          "substitution_applied": {
            "type": "string"
          },
          "original_method": {
            "type": "string"
          }
        },
        "required": [
          "step",
          "instruction",
          "appliance_used",
          "method_used",
          "substitution_applied",
          "original_method"
        ]
      }
    },
    "grocery_list": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item": {
            "type": "string"
          },
          "quantity": {
            "type": "string"
          },
          "category": {
            "type": "string"
          },
          "store_section": {
            "type": "string"
          }
        },
        "required": [
          "item",
          "quantity",
          "category",
          "store_section"
        ]
      }
    }
  },
  "required": [
    "summary",
    "meal_plan",
    "batch_cooking_plan",
    "grocery_list"
  ]
}