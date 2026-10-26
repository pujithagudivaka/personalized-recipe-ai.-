"""
Automated Test Suite for Personalized Recipe Generation Prototype.
Tests:
- Schema validation
- Planner Agent constraint extraction
- Allergen Critic safety guardrail & hidden allergen detection
- Nutrition Auditor macro scoring
- Multi-Agent Orchestrator pipeline execution
"""

import unittest
from models import (
    AllergenAuditResult,
    NutritionInfo,
    PantryInventory,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    UserProfile,
)
from agents import (
    AllergenCriticAgent,
    NutritionAuditorAgent,
    PlannerAgent,
    RecipeOrchestrator,
)


class TestRecipePrototype(unittest.TestCase):

    def setUp(self):
        self.profile = UserProfile(
            user_name="Jordan",
            dietary_preferences=["Gluten-Free", "Dairy-Free"],
            strict_allergens=["Wheat / Gluten", "Dairy / Cow Milk / Butter / Cheese"],
            calorie_target=600,
            target_protein_g=40,
            target_carbs_g=50,
            target_fat_g=20,
            servings=2,
        )
        self.pantry = PantryInventory(
            available_ingredients=["Chicken Breast", "Quinoa", "Broccoli", "Olive Oil", "Garlic"],
            cooking_appliances=["Stovetop", "Oven"],
            max_cooking_time_minutes=30,
            meal_type="Dinner",
            cuisine_preference="Mediterranean",
        )

    def test_planner_agent(self):
        planner = PlannerAgent()
        summary, trace = planner.analyze(self.profile, self.pantry)
        self.assertIn("Gluten-Free", summary)
        self.assertIn("Wheat / Gluten", summary)
        self.assertEqual(trace.agent_name, "Planner & Constraint Parser")
        self.assertEqual(trace.status, "Success")

    def test_allergen_critic_safe_recipe(self):
        critic = AllergenCriticAgent()
        safe_recipe = Recipe(
            title="Safe Grilled Chicken",
            tagline="Gluten & dairy free meal",
            cuisine="Mediterranean",
            prep_time_minutes=10,
            cook_time_minutes=15,
            total_time_minutes=25,
            servings=2,
            difficulty="Easy",
            ingredients=[
                RecipeIngredient(name="Chicken Breast", amount=300, unit="g", in_pantry=True),
                RecipeIngredient(name="Broccoli", amount=200, unit="g", in_pantry=True),
                RecipeIngredient(name="Olive Oil", amount=1, unit="tbsp", in_pantry=True),
            ],
            steps=[RecipeStep(step_number=1, instruction="Grill chicken and steam broccoli.")],
            nutrition=NutritionInfo(
                calories_per_serving=580,
                protein_g=42.0,
                carbs_g=20.0,
                fat_g=18.0,
                fiber_g=6.0,
            ),
            pantry_match_percentage=100.0,
            why_personalized="Tailored without gluten or dairy.",
        )
        audit = critic.audit(safe_recipe, self.profile)
        self.assertTrue(audit.is_safe)
        self.assertFalse(audit.correction_required)
        self.assertEqual(len(audit.flagged_ingredients), 0)

    def test_allergen_critic_catches_hidden_allergen(self):
        critic = AllergenCriticAgent()
        unsafe_recipe = Recipe(
            title="Soy Glazed Chicken",
            tagline="Savory glazed chicken",
            cuisine="Asian",
            prep_time_minutes=5,
            cook_time_minutes=15,
            total_time_minutes=20,
            servings=2,
            difficulty="Easy",
            ingredients=[
                RecipeIngredient(name="Chicken Breast", amount=300, unit="g", in_pantry=True),
                RecipeIngredient(name="Soy Sauce", amount=2, unit="tbsp", in_pantry=True),  # Hidden wheat trap!
                RecipeIngredient(name="Butter", amount=1, unit="tbsp", in_pantry=True),     # Dairy trap!
            ],
            steps=[RecipeStep(step_number=1, instruction="Sauté in butter and glaze with soy sauce.")],
            nutrition=NutritionInfo(
                calories_per_serving=620,
                protein_g=38.0,
                carbs_g=10.0,
                fat_g=24.0,
                fiber_g=1.0,
            ),
            pantry_match_percentage=100.0,
            why_personalized="Glazed chicken test.",
        )
        audit = critic.audit(unsafe_recipe, self.profile)
        self.assertFalse(audit.is_safe)
        self.assertTrue(audit.correction_required)
        self.assertTrue(
            any("soy sauce" in w.lower() for w in audit.hidden_allergen_warnings)
            or any("soy sauce" in w.lower() for w in audit.flagged_ingredients)
        )
        self.assertIsNotNone(audit.corrective_instructions)

    def test_nutrition_auditor(self):
        auditor = NutritionAuditorAgent()
        recipe = Recipe(
            title="Balanced Bowl",
            tagline="Nutritious power bowl",
            cuisine="Mediterranean",
            prep_time_minutes=5,
            cook_time_minutes=15,
            total_time_minutes=20,
            servings=2,
            difficulty="Easy",
            ingredients=[RecipeIngredient(name="Quinoa", amount=150, unit="g", in_pantry=True)],
            steps=[RecipeStep(step_number=1, instruction="Boil quinoa.")],
            nutrition=NutritionInfo(
                calories_per_serving=620,  # +20 from 600 target
                protein_g=42.0,            # +2 from 40 target
                carbs_g=52.0,
                fat_g=21.0,
                fiber_g=7.0,
            ),
            pantry_match_percentage=100.0,
            why_personalized="Nutrition test.",
        )
        audit = auditor.audit(recipe, self.profile)
        self.assertTrue(audit.meets_targets)
        self.assertEqual(audit.calorie_variance, 20)
        self.assertGreaterEqual(audit.health_score, 8.0)

    def test_orchestrator_pipeline(self):
        orchestrator = RecipeOrchestrator()
        result = orchestrator.run_pipeline(self.profile, self.pantry)
        self.assertIsNotNone(result.recipe)
        self.assertTrue(result.allergen_audit.is_safe)
        self.assertGreater(len(result.trace), 3)
        self.assertGreater(result.nutrition_audit.health_score, 0)


if __name__ == "__main__":
    unittest.main()
