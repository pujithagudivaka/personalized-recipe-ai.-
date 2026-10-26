"""
Data models and schemas for Personalized Recipe Generation.
Defines Pydantic models for user profile, pantry inventory, recipe components,
and multi-agent audit results.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DietaryPreference(str, Enum):
    NONE = "None / Omnivore"
    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"
    PESCATARIAN = "Pescatarian"
    KETO = "Ketogenic"
    PALEO = "Paleo"
    LOW_CARB = "Low-Carb"
    MEDITERRANEAN = "Mediterranean"
    GLUTEN_FREE = "Gluten-Free"
    DAIRY_FREE = "Dairy-Free"
    LOW_FODMAP = "Low-FODMAP"
    HALAL = "Halal"
    KOSHER = "Kosher"


class Allergen(str, Enum):
    PEANUTS = "Peanuts"
    TREE_NUTS = "Tree Nuts (Walnuts, Almonds, Cashews, etc.)"
    DAIRY = "Dairy / Cow Milk / Butter / Cheese"
    EGGS = "Eggs"
    WHEAT_GLUTEN = "Wheat / Gluten"
    SOY = "Soy / Soy Sauce / Tofu"
    SHELLFISH = "Shellfish (Shrimp, Crab, Lobster)"
    FISH = "Fish (Salmon, Tuna, Anchovies, etc.)"
    SESAME = "Sesame / Tahini"
    MUSTARD = "Mustard"
    SULFITES = "Sulfites"


class UserProfile(BaseModel):
    user_name: str = "Chef"
    dietary_preferences: List[str] = Field(
        default_factory=lambda: ["Omnivore"],
        description="List of selected dietary restrictions or preferences",
    )
    strict_allergens: List[str] = Field(
        default_factory=list,
        description="Zero-tolerance allergen exclusions",
    )
    disliked_ingredients: List[str] = Field(
        default_factory=list,
        description="Ingredients user prefers not to eat",
    )
    calorie_target: int = Field(default=650, ge=200, le=2500, description="Target calories per serving")
    target_protein_g: int = Field(default=40, ge=5, le=150, description="Target protein in grams")
    target_carbs_g: int = Field(default=60, ge=0, le=250, description="Target carbohydrates in grams")
    target_fat_g: int = Field(default=22, ge=0, le=120, description="Target fat in grams")
    servings: int = Field(default=2, ge=1, le=12, description="Number of portions to prepare")
    skill_level: str = Field(default="Intermediate", description="Cooking proficiency (Beginner, Intermediate, Advanced)")


class PantryInventory(BaseModel):
    available_ingredients: List[str] = Field(
        default_factory=list,
        description="Ingredients currently available at home",
    )
    pantry_staples: List[str] = Field(
        default_factory=lambda: ["Olive Oil", "Salt", "Black Pepper", "Garlic", "Water"],
        description="Basic staples assumed to be present",
    )
    cooking_appliances: List[str] = Field(
        default_factory=lambda: ["Stovetop", "Oven"],
        description="Available cooking equipment",
    )
    max_cooking_time_minutes: int = Field(default=35, ge=10, le=180, description="Maximum total preparation time")
    meal_type: str = Field(default="Dinner", description="Breakfast, Lunch, Dinner, Snack, or Post-Workout")
    cuisine_preference: str = Field(default="Any / Fusion", description="Preferred culinary tradition")


class RecipeIngredient(BaseModel):
    name: str = Field(description="Ingredient name")
    amount: float = Field(description="Numerical quantity")
    unit: str = Field(description="Measurement unit (g, ml, tbsp, cup, piece, etc.)")
    in_pantry: bool = Field(default=True, description="Whether ingredient is in user's pantry")
    substitution_note: Optional[str] = Field(
        default=None,
        description="Culinary substitution advice if user lacks this item or allergen swap",
    )


class RecipeStep(BaseModel):
    step_number: int = Field(description="Step sequence number")
    instruction: str = Field(description="Clear, actionable cooking instruction")
    duration_minutes: Optional[int] = Field(default=None, description="Active cooking duration in minutes")
    chef_tip: Optional[str] = Field(default=None, description="Pro culinary tip or technique reminder")


class NutritionInfo(BaseModel):
    calories_per_serving: int = Field(description="Estimated energy in kcal")
    protein_g: float = Field(description="Estimated protein in grams")
    carbs_g: float = Field(description="Estimated carbohydrates in grams")
    fat_g: float = Field(description="Estimated dietary fat in grams")
    fiber_g: float = Field(default=5.0, description="Estimated dietary fiber in grams")
    macro_balance_rating: str = Field(
        default="Balanced",
        description="Assessment: High-Protein, Low-Carb, Balanced, or Calorie-Dense",
    )


class Recipe(BaseModel):
    title: str = Field(description="Creative, appetizing recipe title")
    tagline: str = Field(description="Short one-line description of the dish")
    cuisine: str = Field(description="Culinary style")
    prep_time_minutes: int = Field(description="Preparation time in minutes")
    cook_time_minutes: int = Field(description="Active cooking time in minutes")
    total_time_minutes: int = Field(description="Total time from start to plate")
    servings: int = Field(description="Number of servings generated for")
    difficulty: str = Field(description="Easy, Medium, or Advanced")
    ingredients: List[RecipeIngredient] = Field(description="Structured ingredient list")
    steps: List[RecipeStep] = Field(description="Ordered cooking instructions")
    nutrition: NutritionInfo = Field(description="Nutritional estimation per serving")
    pantry_match_percentage: float = Field(
        default=100.0,
        description="Percentage of ingredients covered by available pantry",
    )
    why_personalized: str = Field(
        description="Detailed explanation of how this recipe specifically satisfies the user's constraints and pantry",
    )


class AllergenAuditResult(BaseModel):
    is_safe: bool = Field(description="True if zero allergen violations detected")
    flagged_ingredients: List[str] = Field(
        default_factory=list,
        description="List of ingredients violating user's allergen list",
    )
    hidden_allergen_warnings: List[str] = Field(
        default_factory=list,
        description="Warnings regarding hidden allergens (e.g. wheat in soy sauce, fish in Worcestershire)",
    )
    audit_reasoning: str = Field(description="Explanatory audit statement")
    correction_required: bool = Field(default=False, description="Flag indicating recipe must be regenerated")
    corrective_instructions: Optional[str] = Field(
        default=None,
        description="Specific instructions sent to Generator Agent for revision",
    )


class NutritionAuditResult(BaseModel):
    meets_targets: bool = Field(description="Whether recipe is within acceptable margin of calorie/macro targets")
    calorie_variance: int = Field(description="Actual calories minus target calories")
    protein_variance: float = Field(description="Actual protein minus target protein")
    health_score: float = Field(ge=1.0, le=10.0, description="Nutritional quality score from 1.0 to 10.0")
    audit_notes: str = Field(description="Detailed breakdown of macro and micro nutrient alignment")
    suggested_tweaks: List[str] = Field(
        default_factory=list,
        description="Actionable adjustments (e.g. 'Use 1 tbsp less oil to lower fat by 14g')",
    )


class AgentTraceStep(BaseModel):
    agent_name: str = Field(description="Name of the agent (Planner, Generator, Allergen Critic, Nutrition Auditor)")
    phase: str = Field(description="Operational phase")
    status: str = Field(description="Success, Warning, Revision, or Error")
    timestamp: str = Field(description="ISO or formatted execution timestamp")
    decision: str = Field(description="Summary of agent output/decision")
    details: str = Field(description="Detailed reasoning trace or critique")


class OrchestratorResult(BaseModel):
    recipe: Recipe
    allergen_audit: AllergenAuditResult
    nutrition_audit: NutritionAuditResult
    revision_count: int = Field(default=0, description="Number of reflection loops executed")
    trace: List[AgentTraceStep] = Field(default_factory=list, description="Audit trace of all agent interactions")
