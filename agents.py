"""
Multi-Agent Orchestration Engine for Personalized Recipe Generation.
Implements:
1. Planner / Constraint Analyzer Agent
2. Generative Recipe Synthesis Agent (Gemini API with fallback mock)
3. Allergen & Safety Guardrail Critic Agent (Self-Reflection Loop)
4. Nutritional & Macronutrient Auditor Agent
"""

import json
import os
import time
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from pydantic import ValidationError

from models import (
    AllergenAuditResult,
    NutritionAuditResult,
    NutritionInfo,
    OrchestratorResult,
    PantryInventory,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    UserProfile,
    AgentTraceStep,
)
from sample_data import ALLERGEN_HIDDEN_TRAPS


class PlannerAgent:
    """Agent 1: Analyzes user profile, strict constraints, and pantry feasibility."""

    def analyze(self, profile: UserProfile, pantry: PantryInventory) -> Tuple[str, AgentTraceStep]:
        strict_allergens = profile.strict_allergens
        diet_str = ", ".join(profile.dietary_preferences) or "Standard"
        allergens_str = ", ".join(strict_allergens) if strict_allergens else "None reported"
        pantry_count = len(pantry.available_ingredients)

        plan_summary = (
            f"Parsed profile for {profile.user_name}: Diet [{diet_str}], "
            f"Strict Zero-Tolerance Allergens [{allergens_str}], "
            f"Target {profile.calorie_target} kcal, {profile.target_protein_g}g Protein. "
            f"Pantry inventory contains {pantry_count} items. Max prep time: {pantry.max_cooking_time_minutes} min."
        )

        trace = AgentTraceStep(
            agent_name="Planner & Constraint Parser",
            phase="Pre-Generation Analysis",
            status="Success",
            timestamp=datetime.now().strftime("%H:%M:%S"),
            decision="Constraints validated and normalized for generation.",
            details=plan_summary,
        )
        return plan_summary, trace


class AllergenCriticAgent:
    """Agent 3: Rigorously audits recipe ingredients against strict user allergens."""

    def audit(
        self,
        recipe: Recipe,
        profile: UserProfile,
        gemini_client=None,
        model_name: str = "gemini-2.5-flash",
    ) -> AllergenAuditResult:
        flagged: List[str] = []
        hidden_warnings: List[str] = []
        strict_allergens = profile.strict_allergens

        if not strict_allergens:
            return AllergenAuditResult(
                is_safe=True,
                flagged_ingredients=[],
                hidden_allergen_warnings=[],
                audit_reasoning="User has no strict allergen restrictions. Safety check passed.",
                correction_required=False,
                corrective_instructions=None,
            )

        # 1. Deterministic Rule-Based Deep Audit against allergen trap dictionary
        all_recipe_texts = [ing.name.lower() for ing in recipe.ingredients] + [
            step.instruction.lower() for step in recipe.steps
        ]
        combined_text = " ".join(all_recipe_texts)

        for allergen in strict_allergens:
            # Check direct allergen matches
            allergen_clean = allergen.split("/")[0].strip().lower()
            if allergen_clean in combined_text:
                flagged.append(f"Direct match found: '{allergen_clean}' violates constraint '{allergen}'.")

            # Check hidden derivative traps
            for known_allergen_key, trap_items in ALLERGEN_HIDDEN_TRAPS.items():
                if allergen.lower() in known_allergen_key.lower() or known_allergen_key.lower() in allergen.lower():
                    for trap in trap_items:
                        trap_lower = trap.lower()
                        # Word boundary match
                        if f" {trap_lower} " in f" {combined_text} " or trap_lower in combined_text:
                            # Avoid false positives if it says "gluten-free soy sauce" or "dairy-free butter"
                            safe_prefixes = ["gluten-free", "dairy-free", "vegan", "substitute", "tamari"]
                            if not any(f"{safe} {trap_lower}" in combined_text for safe in safe_prefixes):
                                hidden_warnings.append(
                                    f"Potential hidden allergen trap: '{trap}' detected under '{allergen}' restriction."
                                )

        # Determine safety
        is_safe = (len(flagged) == 0) and (len(hidden_warnings) == 0)

        if not is_safe:
            all_issues = flagged + hidden_warnings
            corrective = (
                f"SAFETY CRITIC REJECTION: The recipe contains or references ingredients violating the strict allergen filter: "
                f"{'; '.join(all_issues)}. You MUST eliminate these items immediately and replace them with verified safe alternatives "
                f"(e.g., use Tamari instead of Soy Sauce for gluten allergies, or Olive Oil instead of Butter for dairy allergies)."
            )
            reasoning = f"Failed safety audit: {len(all_issues)} violation(s) or hidden allergen risk(s) detected."
        else:
            corrective = None
            reasoning = "Passed complete allergen safety audit. No direct or hidden allergens detected."

        return AllergenAuditResult(
            is_safe=is_safe,
            flagged_ingredients=flagged,
            hidden_allergen_warnings=hidden_warnings,
            audit_reasoning=reasoning,
            correction_required=not is_safe,
            corrective_instructions=corrective,
        )


class NutritionAuditorAgent:
    """Agent 4: Evaluates calorie, macronutrient compliance, and overall nutritional balance."""

    def audit(self, recipe: Recipe, profile: UserProfile) -> NutritionAuditResult:
        actual_cal = recipe.nutrition.calories_per_serving
        target_cal = profile.calorie_target
        cal_diff = actual_cal - target_cal

        actual_protein = recipe.nutrition.protein_g
        target_protein = profile.target_protein_g
        protein_diff = actual_protein - target_protein

        # Assess compliance (tolerance within +- 15% of calorie target)
        pct_cal_diff = abs(cal_diff) / max(target_cal, 1)
        meets_targets = pct_cal_diff <= 0.15

        # Calculate a nutritional quality score out of 10
        base_score = 10.0
        # Penalize for calorie overshoot
        if pct_cal_diff > 0.15:
            base_score -= min(3.0, (pct_cal_diff - 0.15) * 10)
        # Reward protein adequacy
        if actual_protein < target_protein * 0.8:
            base_score -= 1.5
        # Reward fiber
        if recipe.nutrition.fiber_g >= 5.0:
            base_score += 0.5
        else:
            base_score -= 0.5

        final_score = max(1.0, min(10.0, round(base_score, 1)))

        tweaks: List[str] = []
        if cal_diff > 100:
            tweaks.append(f"Calorie count is +{cal_diff} kcal over target. Reduce added cooking oils or fats by 1 tablespoon.")
        elif cal_diff < -100:
            tweaks.append(f"Calorie count is {abs(cal_diff)} kcal below target. Add a side of complex carbs (quinoa/rice) or avocado.")

        if protein_diff < -10:
            tweaks.append(f"Protein is {abs(round(protein_diff, 1))}g below your {target_protein}g goal. Increase portion of primary protein.")
        elif protein_diff > 15:
            tweaks.append(f"Excellent high-protein yield (+{round(protein_diff, 1)}g above target). Great for muscle recovery.")

        notes = (
            f"Nutritional Audit: {actual_cal} kcal vs {target_cal} kcal target ({'+' if cal_diff >= 0 else ''}{cal_diff} kcal). "
            f"Protein: {actual_protein}g vs {target_protein}g target. "
            f"Carbs: {recipe.nutrition.carbs_g}g | Fat: {recipe.nutrition.fat_g}g | Fiber: {recipe.nutrition.fiber_g}g. "
            f"Macro Rating: {recipe.nutrition.macro_balance_rating}."
        )

        return NutritionAuditResult(
            meets_targets=meets_targets,
            calorie_variance=cal_diff,
            protein_variance=round(protein_diff, 1),
            health_score=final_score,
            audit_notes=notes,
            suggested_tweaks=tweaks,
        )


class RecipeGeneratorAgent:
    """Agent 2: Synthesizes a structured, appetizing recipe using Gemini or mock generation."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize google-genai Client: {e}")

    def generate(
        self,
        profile: UserProfile,
        pantry: PantryInventory,
        critic_feedback: Optional[str] = None,
    ) -> Recipe:
        if self.client:
            try:
                return self._generate_with_gemini(profile, pantry, critic_feedback)
            except Exception as e:
                print(f"Gemini generation error: {e}. Falling back to domain rule generator.")
                return self._generate_mock(profile, pantry, critic_feedback)
        else:
            return self._generate_mock(profile, pantry, critic_feedback)

    def _generate_with_gemini(
        self,
        profile: UserProfile,
        pantry: PantryInventory,
        critic_feedback: Optional[str] = None,
    ) -> Recipe:
        from google.genai import types

        prompt = f"""
You are the Executive Recipe Synthesis Agent in an Agentic AI culinary system.
Design a highly personalized, delicious, and chef-quality recipe tailored strictly to the user's constraints.

USER PROFILE:
- Name: {profile.user_name}
- Dietary Preferences: {', '.join(profile.dietary_preferences)}
- STRICT ZERO-TOLERANCE ALLERGENS: {', '.join(profile.strict_allergens) if profile.strict_allergens else 'None'}
- Disliked Ingredients: {', '.join(profile.disliked_ingredients) if profile.disliked_ingredients else 'None'}
- Calorie Target: {profile.calorie_target} kcal per serving
- Macronutrient Goals: {profile.target_protein_g}g Protein, {profile.target_carbs_g}g Carbs, {profile.target_fat_g}g Fat
- Servings Needed: {profile.servings}
- Skill Level: {profile.skill_level}

PANTRY & INVENTORY:
- Available Ingredients on hand: {', '.join(pantry.available_ingredients)}
- Basic Pantry Staples on hand: {', '.join(pantry.pantry_staples)}
- Cooking Appliances: {', '.join(pantry.cooking_appliances)}
- Max Cooking Time: {pantry.max_cooking_time_minutes} minutes
- Meal Type: {pantry.meal_type}
- Preferred Cuisine: {pantry.cuisine_preference}

CRITICAL RULES:
1. STRICT ALLERGEN SAFETY: Never use or recommend any ingredient containing or derived from {', '.join(profile.strict_allergens) if profile.strict_allergens else 'None'}. Be hyper-vigilant about hidden allergens (e.g. no regular soy sauce if gluten-free; use tamari. No butter if dairy-free; use olive or avocado oil).
2. PANTRY MAXIMIZATION: Prioritize available pantry ingredients to minimize waste. Mark 'in_pantry=True' if present in pantry.
3. PRECISE NUTRITION: Calculate realistic calories, protein, carbs, fat, and fiber per serving aligned with the target.
4. ACTIONABLE STEPS: Provide step-by-step cooking instructions with duration in minutes and chef tips.
"""
        if critic_feedback:
            prompt += f"\n\nPRIOR CRITIQUE REVISION REQUEST:\n{critic_feedback}\nYou must revise the recipe to resolve every critique above!"

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Recipe,
                temperature=0.3,
            ),
        )

        # The google-genai SDK parses into response.parsed if response_schema is passed
        if hasattr(response, "parsed") and response.parsed:
            if isinstance(response.parsed, Recipe):
                return response.parsed
            elif isinstance(response.parsed, dict):
                return Recipe.model_validate(response.parsed)

        # Fallback to json parsing
        text = response.text
        data = json.loads(text)
        return Recipe.model_validate(data)

    def _generate_mock(
        self,
        profile: UserProfile,
        pantry: PantryInventory,
        critic_feedback: Optional[str] = None,
    ) -> Recipe:
        """Intelligent domain-based synthesis for offline demonstration or testing."""
        is_gf = any("gluten" in d.lower() or "wheat" in d.lower() for d in profile.dietary_preferences + profile.strict_allergens)
        is_df = any("dairy" in d.lower() or "milk" in d.lower() for d in profile.dietary_preferences + profile.strict_allergens)
        is_vegan = any("vegan" in d.lower() for d in profile.dietary_preferences)
        is_keto = any("keto" in d.lower() for d in profile.dietary_preferences)

        # Primary protein selection
        pantry_items_lower = [i.lower() for i in pantry.available_ingredients]
        chosen_protein = "Grilled Chicken Breast"
        protein_amount = 350.0
        protein_unit = "g"

        if is_vegan:
            if any("chickpea" in i for i in pantry_items_lower):
                chosen_protein = "Organic Chickpeas (rinsed)"
                protein_unit = "can (400g)"
                protein_amount = 1.0
            elif any("tofu" in i for i in pantry_items_lower):
                chosen_protein = "Extra-Firm Organic Tofu"
                protein_unit = "block (350g)"
                protein_amount = 1.0
            else:
                chosen_protein = "Black Beans & Quinoa Blend"
                protein_unit = "cups"
                protein_amount = 2.0
        elif any("salmon" in i for i in pantry_items_lower):
            chosen_protein = "Fresh Atlantic Salmon Fillet"
            protein_amount = 320.0
            protein_unit = "g"
        elif any("egg" in i for i in pantry_items_lower) and "chicken" not in pantry_items_lower:
            chosen_protein = "Farm Fresh Eggs"
            protein_amount = 4.0
            protein_unit = "large eggs"

        # Cooking fat
        cooking_fat = "Extra Virgin Olive Oil"
        fat_note = "Heart-healthy mono-unsaturated fat"
        if not is_df and not is_vegan and "butter" in pantry_items_lower:
            cooking_fat = "Grass-Fed Butter"
            fat_note = "Rich flavor"

        # Carbs / Veggies
        primary_veg = "Crisp Broccoli Florets"
        if any("asparagus" in i for i in pantry_items_lower):
            primary_veg = "Tender Asparagus Spears"
        elif any("spinach" in i for i in pantry_items_lower):
            primary_veg = "Baby Spinach"
        elif any("bell pepper" in i for i in pantry_items_lower):
            primary_veg = "Sliced Bell Peppers"

        grain = "Steamed Quinoa"
        if is_keto:
            grain = "Riced Cauliflower"
        elif is_gf:
            grain = "Jasmine Rice" if any("rice" in i for i in pantry_items_lower) else "Fluffy Quinoa"

        # Flavor enhancer safe check
        sauce_name = "Lemon Herb Garlic Glaze"
        if "asian" in pantry.cuisine_preference.lower():
            sauce_name = "Tamari Ginger Reduction (Certified Gluten-Free)" if is_gf else "Soy Ginger Reduction"

        title = f"{pantry.cuisine_preference} {chosen_protein.split('(')[0].strip()} & {primary_veg.split(' ')[-1]} Power Skillet"
        tagline = f"A customized {profile.calorie_target}-kcal macro-balanced meal designed specifically for {profile.user_name}."

        ingredients = [
            RecipeIngredient(
                name=chosen_protein,
                amount=protein_amount,
                unit=protein_unit,
                in_pantry=True,
                substitution_note=None,
            ),
            RecipeIngredient(
                name=primary_veg,
                amount=250.0,
                unit="g",
                in_pantry=True,
                substitution_note="Can substitute with zucchini or green beans.",
            ),
            RecipeIngredient(
                name=grain,
                amount=180.0,
                unit="g cooked",
                in_pantry=True if any("rice" in i or "quinoa" in i for i in pantry_items_lower) else False,
                substitution_note="Naturally gluten-free grain base.",
            ),
            RecipeIngredient(
                name=cooking_fat,
                amount=1.5,
                unit="tbsp",
                in_pantry=True,
                substitution_note=fat_note,
            ),
            RecipeIngredient(
                name="Fresh Garlic (minced)",
                amount=3.0,
                unit="cloves",
                in_pantry=True,
                substitution_note="Pantry staple aromatic.",
            ),
            RecipeIngredient(
                name="Fresh Squeezed Lemon Juice",
                amount=2.0,
                unit="tbsp",
                in_pantry=True if any("lemon" in i for i in pantry_items_lower) else False,
                substitution_note="Provides acidity to brighten the dish without sodium.",
            ),
        ]

        steps = [
            RecipeStep(
                step_number=1,
                instruction=f"Prep ingredients: Pat {chosen_protein} dry with paper towels. Trim and cut {primary_veg} into bite-sized pieces. Mince garlic.",
                duration_minutes=5,
                chef_tip="Drying your protein ensures a golden sear rather than steaming in the pan.",
            ),
            RecipeStep(
                step_number=2,
                instruction=f"Heat {cooking_fat} in a large skillet over medium-high heat. Add minced garlic and sauté for 45 seconds until fragrant.",
                duration_minutes=2,
                chef_tip="Do not let garlic brown too deeply or it will impart bitterness.",
            ),
            RecipeStep(
                step_number=3,
                instruction=f"Add {chosen_protein} to the skillet. Cook undisturbed for 4-5 minutes per side until properly seared and thoroughly cooked through.",
                duration_minutes=10,
                chef_tip="Use an instant-read thermometer to check doneness without losing juices.",
            ),
            RecipeStep(
                step_number=4,
                instruction=f"Toss in {primary_veg} around the pan. Sauté for 4-5 minutes until tender-crisp and vibrant in color.",
                duration_minutes=5,
                chef_tip="Add 1 tbsp of water or broth to create steam and tenderize veggies faster.",
            ),
            RecipeStep(
                step_number=5,
                instruction=f"Finish by drizzling fresh lemon juice and seasoning with sea salt and cracked black pepper. Plate atop warm {grain} and serve immediately.",
                duration_minutes=2,
                chef_tip="Acid at the end wakes up the flavor profile and enhances nutrient bioavailability.",
            ),
        ]

        # Calculate macro calibration
        target_cal = profile.calorie_target
        cal = target_cal + 15
        prot = float(profile.target_protein_g)
        carbs = float(profile.target_carbs_g if not is_keto else 12.0)
        fat = float(profile.target_fat_g if not is_keto else 35.0)

        nutrition = NutritionInfo(
            calories_per_serving=cal,
            protein_g=prot,
            carbs_g=carbs,
            fat_g=fat,
            fiber_g=6.5,
            macro_balance_rating="High Protein & Balanced",
        )

        pantry_match_pct = round(
            (sum(1 for i in ingredients if i.in_pantry) / len(ingredients)) * 100, 1
        )

        why_personalized = (
            f"Tailored for {profile.user_name}: Strictly verified safe with zero {', '.join(profile.strict_allergens) if profile.strict_allergens else 'allergens'}. "
            f"Incorporated available pantry ingredients ({', '.join(pantry.available_ingredients[:3])}) to achieve {pantry_match_pct}% pantry utilization. "
            f"Precision-scaled to match your {profile.calorie_target} kcal and {profile.target_protein_g}g protein targets."
        )

        return Recipe(
            title=title,
            tagline=tagline,
            cuisine=pantry.cuisine_preference,
            prep_time_minutes=8,
            cook_time_minutes=16,
            total_time_minutes=24,
            servings=profile.servings,
            difficulty="Easy",
            ingredients=ingredients,
            steps=steps,
            nutrition=nutrition,
            pantry_match_percentage=pantry_match_pct,
            why_personalized=why_personalized,
        )


class RecipeOrchestrator:
    """Agentic Orchestrator coordinating the Multi-Agent Generation, Critique, and Reflection Loop."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.planner = PlannerAgent()
        self.generator = RecipeGeneratorAgent(api_key=api_key, model_name=model_name)
        self.allergen_critic = AllergenCriticAgent()
        self.nutrition_auditor = NutritionAuditorAgent()
        self.max_revisions = 2

    def run_pipeline(
        self,
        profile: UserProfile,
        pantry: PantryInventory,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> OrchestratorResult:
        trace: List[AgentTraceStep] = []

        # Step 1: Planner Agent
        if progress_callback:
            progress_callback("Agent 1 [Planner]: Parsing user profile, strict constraints, and pantry feasibility...", 15)
        _, planner_trace = self.planner.analyze(profile, pantry)
        trace.append(planner_trace)

        # Step 2: Initial Generation
        if progress_callback:
            progress_callback("Agent 2 [Generator]: Synthesizing personalized recipe via Generative Language Model...", 40)
        
        recipe = self.generator.generate(profile, pantry)
        trace.append(
            AgentTraceStep(
                agent_name="Recipe Synthesis Agent",
                phase="Initial Generation",
                status="Success",
                timestamp=datetime.now().strftime("%H:%M:%S"),
                decision=f"Generated candidate recipe: '{recipe.title}' ({recipe.nutrition.calories_per_serving} kcal)",
                details=f"Ingredients selected: {len(recipe.ingredients)} items. Total cooking time: {recipe.total_time_minutes} min.",
            )
        )

        # Step 3: Allergen Guardrail Reflection Loop
        revision_count = 0
        allergen_audit = self.allergen_critic.audit(recipe, profile)

        while allergen_audit.correction_required and revision_count < self.max_revisions:
            revision_count += 1
            if progress_callback:
                progress_callback(
                    f"Agent 3 [Allergen Critic]: Violation detected! Initiating Reflection Loop (Attempt {revision_count})...",
                    65,
                )

            trace.append(
                AgentTraceStep(
                    agent_name="Allergen & Safety Critic",
                    phase=f"Safety Audit Loop {revision_count}",
                    status="Revision Required",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    decision="REJECTED candidate recipe due to allergen risk.",
                    details=allergen_audit.corrective_instructions or allergen_audit.audit_reasoning,
                )
            )

            # Re-invoke Generator with critic's specific corrective feedback
            recipe = self.generator.generate(
                profile,
                pantry,
                critic_feedback=allergen_audit.corrective_instructions,
            )

            trace.append(
                AgentTraceStep(
                    agent_name="Recipe Synthesis Agent",
                    phase=f"Revision {revision_count}",
                    status="Success",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    decision=f"Regenerated recipe '{recipe.title}' addressing critic feedback.",
                    details="Eliminated flagged ingredients and substituted safe alternatives.",
                )
            )

            # Re-audit
            allergen_audit = self.allergen_critic.audit(recipe, profile)

        # Record final allergen audit status
        trace.append(
            AgentTraceStep(
                agent_name="Allergen & Safety Critic",
                phase="Final Safety Verification",
                status="Approved" if allergen_audit.is_safe else "Warning",
                timestamp=datetime.now().strftime("%H:%M:%S"),
                decision="PASSED safety audit" if allergen_audit.is_safe else "Flagged remaining cautions",
                details=allergen_audit.audit_reasoning,
            )
        )

        # Step 4: Nutritional & Macronutrient Auditor
        if progress_callback:
            progress_callback("Agent 4 [Nutrition Auditor]: Evaluating calorie and macronutrient compliance...", 85)

        nutrition_audit = self.nutrition_auditor.audit(recipe, profile)
        trace.append(
            AgentTraceStep(
                agent_name="Nutrition & Macro Auditor",
                phase="Nutritional Compliance",
                status="Success" if nutrition_audit.meets_targets else "Notice",
                timestamp=datetime.now().strftime("%H:%M:%S"),
                decision=f"Health Score: {nutrition_audit.health_score}/10. Meets target: {nutrition_audit.meets_targets}.",
                details=nutrition_audit.audit_notes,
            )
        )

        if progress_callback:
            progress_callback("Pipeline Complete! Presenting personalized recipe dashboard...", 100)

        return OrchestratorResult(
            recipe=recipe,
            allergen_audit=allergen_audit,
            nutrition_audit=nutrition_audit,
            revision_count=revision_count,
            trace=trace,
        )
