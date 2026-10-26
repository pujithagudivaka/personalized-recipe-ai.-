"""
Sample presets and culinary test cases for testing the Personalized Recipe Generation prototype.
"""

from typing import Dict, Any

SAMPLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "Gluten & Dairy Free High-Protein": {
        "user_name": "Alex",
        "dietary_preferences": ["Gluten-Free", "Dairy-Free"],
        "strict_allergens": ["Wheat / Gluten", "Dairy / Cow Milk / Butter / Cheese"],
        "disliked_ingredients": ["Mushrooms"],
        "calorie_target": 650,
        "target_protein_g": 48,
        "target_carbs_g": 50,
        "target_fat_g": 20,
        "servings": 2,
        "skill_level": "Intermediate",
        "available_ingredients": ["Chicken Breast", "Quinoa", "Broccoli", "Avocado", "Garlic", "Lemon"],
        "cooking_appliances": ["Stovetop", "Oven"],
        "max_cooking_time_minutes": 30,
        "meal_type": "Dinner",
        "cuisine_preference": "Mediterranean",
    },
    "Zero-Waste Pantry Rescue": {
        "user_name": "Jordan",
        "dietary_preferences": ["None / Omnivore"],
        "strict_allergens": [],
        "disliked_ingredients": [],
        "calorie_target": 550,
        "target_protein_g": 28,
        "target_carbs_g": 65,
        "target_fat_g": 18,
        "servings": 2,
        "skill_level": "Beginner",
        "available_ingredients": ["Eggs", "Canned Black Beans", "Bell Pepper", "Red Onion", "Cooked Jasmine Rice", "Salsa"],
        "cooking_appliances": ["Stovetop", "Microwave"],
        "max_cooking_time_minutes": 20,
        "meal_type": "Lunch",
        "cuisine_preference": "Mexican / Tex-Mex",
    },
    "Keto Weeknight Quick Bowl": {
        "user_name": "Morgan",
        "dietary_preferences": ["Ketogenic", "Low-Carb"],
        "strict_allergens": ["Peanuts", "Soy / Soy Sauce / Tofu"],
        "disliked_ingredients": ["Cilantro"],
        "calorie_target": 580,
        "target_protein_g": 42,
        "target_carbs_g": 12,
        "target_fat_g": 38,
        "servings": 1,
        "skill_level": "Beginner",
        "available_ingredients": ["Salmon Fillet", "Asparagus", "Zucchini", "Olive Oil", "Lemon", "Garlic Powder"],
        "cooking_appliances": ["Air Fryer", "Stovetop"],
        "max_cooking_time_minutes": 25,
        "meal_type": "Dinner",
        "cuisine_preference": "Contemporary American",
    },
    "Vegan Nut-Free Nutrient Feast": {
        "user_name": "Sam",
        "dietary_preferences": ["Vegan", "Dairy-Free"],
        "strict_allergens": ["Tree Nuts (Walnuts, Almonds, Cashews, etc.)", "Peanuts", "Eggs"],
        "disliked_ingredients": ["Eggplant"],
        "calorie_target": 600,
        "target_protein_g": 30,
        "target_carbs_g": 75,
        "target_fat_g": 16,
        "servings": 2,
        "skill_level": "Intermediate",
        "available_ingredients": ["Canned Chickpeas", "Spinach", "Tomatoes", "Garlic", "Coconut Milk", "Brown Rice", "Curry Powder"],
        "cooking_appliances": ["Stovetop"],
        "max_cooking_time_minutes": 35,
        "meal_type": "Dinner",
        "cuisine_preference": "Indian / Curry",
    },
}

COMMON_PANTRY_ITEMS = [
    "Chicken Breast", "Ground Turkey", "Salmon Fillet", "Tofu", "Eggs", "Canned Chickpeas",
    "Canned Black Beans", "Jasmine Rice", "Quinoa", "Pasta", "Rolled Oats",
    "Broccoli", "Spinach", "Bell Pepper", "Onion", "Garlic", "Tomatoes", "Zucchini", "Carrots", "Avocado",
    "Olive Oil", "Soy Sauce", "Tamari", "Lemon Juice", "Coconut Milk", "Cheddar Cheese"
]

ALLERGEN_HIDDEN_TRAPS = {
    "Wheat / Gluten": ["Soy Sauce", "Worcestershire Sauce", "Beer", "Flour Tortillas", "Breadcrumbs", "Panko", "Couscous", "Seitan", "Malt Vinegar"],
    "Dairy / Cow Milk / Butter / Cheese": ["Butter", "Ghee", "Whey", "Casein", "Yogurt", "Cream", "Parmesan", "Milk Chocolate", "Buttermilk"],
    "Peanuts": ["Peanut Oil (unrefined)", "Arachis Oil", "Peanut Butter", "Satay Sauce"],
    "Tree Nuts (Walnuts, Almonds, Cashews, etc.)": ["Pesto (usually pine nuts or walnuts)", "Almond Milk", "Marzipan", "Praline", "Nutella", "Cashew Cream"],
    "Soy / Soy Sauce / Tofu": ["Edamame", "Miso", "Tempeh", "Soy Protein Isolate", "Teriyaki Sauce"],
    "Eggs": ["Mayonnaise", "Meringue", "Aioli", "Egg Wash", "Hollandaise", "Brioche"],
    "Fish (Salmon, Tuna, Anchovies, etc.)": ["Worcestershire Sauce (anchovies)", "Fish Sauce", "Caesar Salad Dressing (anchovies)", "Kimchi (often contains fish/shrimp)"],
    "Shellfish (Shrimp, Crab, Lobster)": ["Oyster Sauce", "Shrimp Paste", "Bouillabaisse", "XO Sauce"],
    "Sesame / Tahini": ["Tahini", "Hummus (usually contains tahini)", "Gomasio", "Halva", "Sesame Oil"],
}
