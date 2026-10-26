"""
Streamlit Web Application for Personalized Recipe Generation Using a Generative Language Model.
Domain: Generative AI & Agentic AI Systems.
"""

import json
import os
import sys
from datetime import datetime
import plotly.graph_objects as go
import streamlit as st

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import (
    Allergen,
    DietaryPreference,
    PantryInventory,
    UserProfile,
)
from sample_data import COMMON_PANTRY_ITEMS, SAMPLE_PRESETS
from agents import RecipeOrchestrator

# Configure Page
st.set_page_config(
    page_title="NutriAgent AI - Personalized Recipe Generation",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-green { background-color: #DCFCE7; color: #166534; }
    .badge-blue { background-color: #DBEAFE; color: #1E40AF; }
    .badge-amber { background-color: #FEF3C7; color: #92400E; }
    .badge-purple { background-color: #F3E8FF; color: #6B21A8; }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 10px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        text-align: center;
    }
    .step-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .tip-box {
        background-color: #EFF6FF;
        border-left: 3px solid #2563EB;
        padding: 8px 12px;
        font-size: 0.88rem;
        color: #1E40AF;
        border-radius: 4px;
        margin-top: 6px;
    }
    .agent-trace-row {
        padding: 10px 14px;
        border-bottom: 1px solid #E2E8F0;
        font-family: monospace;
        font-size: 0.85rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize Session State
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.user_name = "Alex"
    st.session_state.dietary_preferences = ["Gluten-Free", "Dairy-Free"]
    st.session_state.strict_allergens = ["Wheat / Gluten", "Dairy / Cow Milk / Butter / Cheese"]
    st.session_state.dislikes = "Mushrooms"
    st.session_state.calorie_target = 650
    st.session_state.protein_target = 48
    st.session_state.carbs_target = 50
    st.session_state.fat_target = 20
    st.session_state.servings = 2
    st.session_state.skill_level = "Intermediate"
    st.session_state.available_ingredients = ["Chicken Breast", "Quinoa", "Broccoli", "Avocado", "Garlic", "Lemon"]
    st.session_state.cooking_appliances = ["Stovetop", "Oven"]
    st.session_state.max_time = 30
    st.session_state.meal_type = "Dinner"
    st.session_state.cuisine = "Mediterranean"
    st.session_state.last_result = None


def load_preset(preset_key: str):
    if preset_key in SAMPLE_PRESETS:
        p = SAMPLE_PRESETS[preset_key]
        st.session_state.user_name = p["user_name"]
        st.session_state.dietary_preferences = p["dietary_preferences"]
        st.session_state.strict_allergens = p["strict_allergens"]
        st.session_state.dislikes = ", ".join(p.get("disliked_ingredients", []))
        st.session_state.calorie_target = p["calorie_target"]
        st.session_state.protein_target = p["target_protein_g"]
        st.session_state.carbs_target = p["target_carbs_g"]
        st.session_state.fat_target = p["target_fat_g"]
        st.session_state.servings = p["servings"]
        st.session_state.skill_level = p["skill_level"]
        st.session_state.available_ingredients = p["available_ingredients"]
        st.session_state.cooking_appliances = p["cooking_appliances"]
        st.session_state.max_time = p["max_cooking_time_minutes"]
        st.session_state.meal_type = p["meal_type"]
        st.session_state.cuisine = p["cuisine_preference"]
        st.session_state.last_result = None


# ==========================================
# SIDEBAR: CONFIGURATION & USER PROFILE
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Generative AI Engine")
    engine_mode = st.radio(
        "Model Orchestration Backend",
        ["Google Gemini API (Live)", "Interactive Demo Engine (Offline Mock)"],
        index=0 if os.getenv("GEMINI_API_KEY") else 1,
        help="Use Google Gemini API for live multi-agent LLM synthesis, or Offline Mock for instant offline testing without an API key.",
    )

    api_key_input = ""
    model_choice = "gemini-2.5-flash"
    if engine_mode == "Google Gemini API (Live)":
        env_key = os.getenv("GEMINI_API_KEY", "")
        api_key_input = st.text_input(
            "Gemini API Key",
            value=env_key,
            type="password",
            help="Enter your Google Gemini API key or set GEMINI_API_KEY environment variable.",
        )
        model_choice = st.selectbox(
            "Model Selection",
            ["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0,
            help="Gemini 2.5 Flash is recommended for fast structured JSON outputs and multi-agent loops.",
        )
        if not api_key_input:
            st.info("💡 Note: If no key is entered, the pipeline will seamlessly utilize the intelligent domain rule generator.")

    st.markdown("---")
    st.markdown("### 👤 User Profile & Health Goals")

    st.session_state.user_name = st.text_input("Name", value=st.session_state.user_name)

    diet_options = [d.value for d in DietaryPreference]
    st.session_state.dietary_preferences = st.multiselect(
        "Dietary Lifestyle",
        options=diet_options,
        default=[d for d in st.session_state.dietary_preferences if d in diet_options],
    )

    allergen_options = [a.value for a in Allergen]
    st.session_state.strict_allergens = st.multiselect(
        "🚨 Strict Zero-Tolerance Allergens",
        options=allergen_options,
        default=[a for a in st.session_state.strict_allergens if a in allergen_options],
        help="The Allergen Critic Agent enforces strict zero-tolerance on these ingredients and triggers a reflection loop if violated.",
    )

    st.session_state.dislikes = st.text_input(
        "Disliked Ingredients",
        value=st.session_state.dislikes,
        help="Comma-separated ingredients to exclude if possible.",
    )

    st.markdown("#### 🎯 Calorie & Macronutrient Targets")
    st.session_state.calorie_target = st.slider(
        "Calories per Serving (kcal)",
        min_value=250,
        max_value=1200,
        value=st.session_state.calorie_target,
        step=25,
    )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.session_state.protein_target = st.number_input(
            "Protein (g)",
            min_value=10,
            max_value=120,
            value=st.session_state.protein_target,
        )
        st.session_state.carbs_target = st.number_input(
            "Carbs (g)",
            min_value=0,
            max_value=200,
            value=st.session_state.carbs_target,
        )
    with col_m2:
        st.session_state.fat_target = st.number_input(
            "Fat (g)",
            min_value=5,
            max_value=100,
            value=st.session_state.fat_target,
        )
        st.session_state.servings = st.number_input(
            "Portions",
            min_value=1,
            max_value=8,
            value=st.session_state.servings,
        )

    st.session_state.skill_level = st.selectbox(
        "Culinary Skill Level",
        ["Beginner", "Intermediate", "Advanced"],
        index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.skill_level),
    )


# ==========================================
# MAIN INTERFACE
# ==========================================
st.markdown('<div class="main-header">🍳 NutriAgent AI: Personalized Recipe Generation System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Generative AI & Agentic AI Systems | Multi-Agent Reflection Loop & Safety Guardrail Prototype</div>',
    unsafe_allow_html=True,
)

# Preset Quick Selector
st.markdown("##### ⚡ Quick-Load Test Profiles & Scenarios")
p_cols = st.columns(4)
with p_cols[0]:
    if st.button("🛡️ Celiac & Dairy-Free", use_container_width=True):
        load_preset("Gluten & Dairy Free High-Protein")
        st.rerun()
with p_cols[1]:
    if st.button("♻️ Zero-Waste Pantry", use_container_width=True):
        load_preset("Zero-Waste Pantry Rescue")
        st.rerun()
with p_cols[2]:
    if st.button("🥑 Keto Quick Bowl", use_container_width=True):
        load_preset("Keto Weeknight Quick Bowl")
        st.rerun()
with p_cols[3]:
    if st.button("🌿 Vegan Nut-Free", use_container_width=True):
        load_preset("Vegan Nut-Free Nutrient Feast")
        st.rerun()

st.markdown("---")

tab1, tab2 = st.tabs(["🛒 Pantry Inventory & Recipe Synthesis", "🔬 Multi-Agent Architecture & Audit Trace"])

with tab1:
    col_left, col_right = st.columns([1.2, 0.8])

    with col_left:
        st.markdown("### 1. Pantry & Available Ingredients")
        selected_ingredients = st.multiselect(
            "Select ingredients currently available in your kitchen:",
            options=sorted(list(set(COMMON_PANTRY_ITEMS + st.session_state.available_ingredients))),
            default=st.session_state.available_ingredients,
            help="The Recipe Synthesis Agent will prioritize these items to minimize food waste.",
        )
        st.session_state.available_ingredients = selected_ingredients

        custom_item = st.text_input(
            "Add custom ingredient to pantry (press enter to add):",
            placeholder="e.g. Edamame, Sweet Potato, Kimchi...",
        )
        if custom_item and custom_item.strip() not in st.session_state.available_ingredients:
            st.session_state.available_ingredients.append(custom_item.strip())
            st.rerun()

    with col_right:
        st.markdown("### 2. Cooking Parameters")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.meal_type = st.selectbox(
                "Meal Type",
                ["Breakfast", "Lunch", "Dinner", "Snack", "Post-Workout"],
                index=["Breakfast", "Lunch", "Dinner", "Snack", "Post-Workout"].index(st.session_state.meal_type),
            )
            st.session_state.max_time = st.slider(
                "Max Cooking Time (mins)",
                10,
                90,
                st.session_state.max_time,
                step=5,
            )
        with c2:
            cuisine_options = ["Any / Fusion", "Mediterranean", "Italian", "Mexican / Tex-Mex", "Asian / Stir-Fry", "Indian / Curry", "Contemporary American"]
            current_c = st.session_state.cuisine if st.session_state.cuisine in cuisine_options else "Any / Fusion"
            st.session_state.cuisine = st.selectbox("Cuisine Preference", cuisine_options, index=cuisine_options.index(current_c))

            appliance_options = ["Stovetop", "Oven", "Air Fryer", "Microwave", "Blender", "Pressure Cooker"]
            st.session_state.cooking_appliances = st.multiselect(
                "Available Appliances",
                appliance_options,
                default=[a for a in st.session_state.cooking_appliances if a in appliance_options],
            )

    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("🚀 Run Multi-Agent Recipe Generation Pipeline", type="primary", use_container_width=True)

    # Execution Container
    if generate_btn:
        progress_container = st.container()
        progress_bar = progress_container.progress(5)
        status_text = progress_container.empty()

        def update_progress(msg: str, val: int):
            status_text.markdown(f"**🔄 {msg}**")
            progress_bar.progress(val)

        # Assemble schemas
        profile = UserProfile(
            user_name=st.session_state.user_name,
            dietary_preferences=st.session_state.dietary_preferences,
            strict_allergens=st.session_state.strict_allergens,
            disliked_ingredients=[d.strip() for d in st.session_state.dislikes.split(",") if d.strip()],
            calorie_target=st.session_state.calorie_target,
            target_protein_g=st.session_state.protein_target,
            target_carbs_g=st.session_state.carbs_target,
            target_fat_g=st.session_state.fat_target,
            servings=st.session_state.servings,
            skill_level=st.session_state.skill_level,
        )

        pantry = PantryInventory(
            available_ingredients=st.session_state.available_ingredients,
            cooking_appliances=st.session_state.cooking_appliances,
            max_cooking_time_minutes=st.session_state.max_time,
            meal_type=st.session_state.meal_type,
            cuisine_preference=st.session_state.cuisine,
        )

        orchestrator = RecipeOrchestrator(
            api_key=api_key_input if engine_mode == "Google Gemini API (Live)" else None,
            model_name=model_choice,
        )

        try:
            result = orchestrator.run_pipeline(profile, pantry, progress_callback=update_progress)
            st.session_state.last_result = result
            progress_container.empty()
            st.success("🎉 Recipe Synthesized and Multi-Agent Audits Completed Successfully!")
        except Exception as e:
            progress_container.empty()
            st.error(f"Execution Error: {str(e)}")

    # Display Recipe Dashboard if result exists
    if st.session_state.last_result:
        res = st.session_state.last_result
        recipe = res.recipe
        allergen_audit = res.allergen_audit
        nutrition_audit = res.nutrition_audit

        st.markdown("---")
        st.markdown(f"## 🍽️ {recipe.title}")
        st.markdown(f"*{recipe.tagline}*")

        # Key Badges & Metrics
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.markdown(
                f'<div class="metric-card"><div style="font-size:0.85rem;color:#64748B;">Total Time</div><div style="font-size:1.4rem;font-weight:700;color:#1E293B;">⏱️ {recipe.total_time_minutes} min</div><div style="font-size:0.75rem;color:#94A3B8;">Prep: {recipe.prep_time_minutes}m | Cook: {recipe.cook_time_minutes}m</div></div>',
                unsafe_allow_html=True,
            )
        with b2:
            st.markdown(
                f'<div class="metric-card"><div style="font-size:0.85rem;color:#64748B;">Pantry Utilization</div><div style="font-size:1.4rem;font-weight:700;color:#166534;">📦 {recipe.pantry_match_percentage}%</div><div style="font-size:0.75rem;color:#94A3B8;">Minimizes Food Waste</div></div>',
                unsafe_allow_html=True,
            )
        with b3:
            allergen_color = "#166534" if allergen_audit.is_safe else "#DC2626"
            allergen_status = "SAFE: Passed" if allergen_audit.is_safe else "REVISION FLAGGED"
            st.markdown(
                f'<div class="metric-card"><div style="font-size:0.85rem;color:#64748B;">Allergen Guardrail</div><div style="font-size:1.3rem;font-weight:700;color:{allergen_color};">🛡️ {allergen_status}</div><div style="font-size:0.75rem;color:#94A3B8;">Zero Cross-Contamination</div></div>',
                unsafe_allow_html=True,
            )
        with b4:
            st.markdown(
                f'<div class="metric-card"><div style="font-size:0.85rem;color:#64748B;">Nutritional Quality Score</div><div style="font-size:1.4rem;font-weight:700;color:#2563EB;">⭐ {nutrition_audit.health_score} / 10</div><div style="font-size:0.75rem;color:#94A3B8;">Macro Compliance</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"💡 **Why This Recipe is Personalized For You:** {recipe.why_personalized}")

        # 3 Column Breakdown: Ingredients, Steps, Nutrition
        c_ing, c_steps, c_nut = st.columns([1, 1.4, 1.1])

        with c_ing:
            st.markdown("### 🛒 Ingredients")
            for ing in recipe.ingredients:
                badge = "🟢 Pantry" if ing.in_pantry else "🟠 Needed"
                sub_text = f"<br><small style='color:#64748B;'>*Swap: {ing.substitution_note}*</small>" if ing.substitution_note else ""
                st.markdown(
                    f"- **{ing.amount} {ing.unit}** {ing.name} `[{badge}]`{sub_text}",
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown(f"**Servings:** {recipe.servings} | **Difficulty:** {recipe.difficulty}")

        with c_steps:
            st.markdown("### 👨‍🍳 Step-by-Step Cooking Guide")
            for step in recipe.steps:
                st.checkbox(f"**Step {step.step_number}** ({step.duration_minutes or 3} mins)", value=False, key=f"step_{step.step_number}")
                st.write(step.instruction)
                if step.chef_tip:
                    st.markdown(f'<div class="tip-box">💡 <b>Chef Tip:</b> {step.chef_tip}</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

        with c_nut:
            st.markdown("### 📊 Nutritional Breakdown")
            nut = recipe.nutrition

            # Target vs Actual Metrics
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                st.metric("Calories", f"{nut.calories_per_serving} kcal", delta=f"{nutrition_audit.calorie_variance} kcal")
                st.metric("Carbs", f"{nut.carbs_g} g")
            with col_act2:
                st.metric("Protein", f"{nut.protein_g} g", delta=f"{nutrition_audit.protein_variance} g")
                st.metric("Fat", f"{nut.fat_g} g")

            st.caption(f"Fiber: {nut.fiber_g}g | Macro Balance: {nut.macro_balance_rating}")

            # Donut Chart for Macros
            labels = ["Protein", "Carbohydrates", "Fat"]
            values = [nut.protein_g * 4, nut.carbs_g * 4, nut.fat_g * 9]  # Calories from each
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.6,
                        marker=dict(colors=["#3B82F6", "#10B981", "#F59E0B"]),
                        textinfo="label+percent",
                    )
                ]
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=220,
            )
            st.plotly_chart(fig, use_container_width=True)

            if nutrition_audit.suggested_tweaks:
                st.markdown("**Actionable Nutritional Tweaks:**")
                for tweak in nutrition_audit.suggested_tweaks:
                    st.markdown(f"- <small>{tweak}</small>", unsafe_allow_html=True)

        # Export Section
        st.markdown("---")
        exp_col1, exp_col2, _ = st.columns([1, 1, 2])
        with exp_col1:
            recipe_md = f"# {recipe.title}\n*{recipe.tagline}*\n\n"
            recipe_md += f"**Cuisine:** {recipe.cuisine} | **Total Time:** {recipe.total_time_minutes} min | **Servings:** {recipe.servings}\n\n"
            recipe_md += f"### Ingredients\n"
            for ing in recipe.ingredients:
                recipe_md += f"- {ing.amount} {ing.unit} {ing.name} {'(In Pantry)' if ing.in_pantry else '(Needed)'}\n"
            recipe_md += f"\n### Preparation Steps\n"
            for step in recipe.steps:
                recipe_md += f"{step.step_number}. {step.instruction}\n"
            recipe_md += f"\n### Nutrition per serving\n- Calories: {nut.calories_per_serving} kcal\n- Protein: {nut.protein_g}g\n- Carbs: {nut.carbs_g}g\n- Fat: {nut.fat_g}g\n"
            st.download_button(
                "📥 Download Recipe Card (.md)",
                data=recipe_md,
                file_name=f"{recipe.title.lower().replace(' ', '_')}.md",
                mime="text/markdown",
            )
        with exp_col2:
            st.download_button(
                "📥 Download Structured JSON",
                data=json.dumps(recipe.model_dump(), indent=2),
                file_name=f"{recipe.title.lower().replace(' ', '_')}.json",
                mime="application/json",
            )


# ==========================================
# TAB 2: AGENTIC ARCHITECTURE & AUDIT TRACE
# ==========================================
with tab2:
    st.markdown("### 🔬 Multi-Agent AI System Architecture")
    st.markdown(
        """
        This prototype demonstrates an **Agentic Generative AI workflow** featuring self-reflection,
        constraint satisfaction, and automated guardrail audits.
        """
    )

    # Architecture Overview Cards
    arch1, arch2, arch3, arch4 = st.columns(4)
    with arch1:
        st.markdown(
            """
            <div class="metric-card" style="text-align:left;">
                <div style="font-weight:700;color:#1E40AF;">1. Planner Agent</div>
                <small>Parses user dietary preferences, strict zero-tolerance allergens, and calculates pantry inventory coverage.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with arch2:
        st.markdown(
            """
            <div class="metric-card" style="text-align:left;">
                <div style="font-weight:700;color:#047857;">2. Synthesis Agent</div>
                <small>Generates structured, appetizing culinary recipes adhering to pantry ingredients and target nutritional ratios.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with arch3:
        st.markdown(
            """
            <div class="metric-card" style="text-align:left;">
                <div style="font-weight:700;color:#B45309;">3. Allergen Critic</div>
                <small>Rigorous safety guardrail scanning for direct matches and hidden traps (e.g. soy sauce wheat, oyster sauce fish).</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with arch4:
        st.markdown(
            """
            <div class="metric-card" style="text-align:left;">
                <div style="font-weight:700;color:#6B21A8;">4. Nutrition Auditor</div>
                <small>Evaluates calorie and macro variances against user targets, scores nutritional quality, and suggests tweaks.</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Live Agent Execution Trace & Reflection Log")

    if st.session_state.last_result:
        res = st.session_state.last_result
        st.write(f"**Total Agent Iterations & Reflections Executed:** `{len(res.trace)}` | **Revision Loops:** `{res.revision_count}`")

        for i, step in enumerate(res.trace):
            status_badge = "badge-green" if step.status == "Success" or step.status == "Approved" else "badge-amber"
            if step.status == "Revision Required":
                status_badge = "badge-purple"

            with st.expander(f"Step {i+1}: [{step.agent_name}] - {step.phase} ({step.status})", expanded=True):
                st.markdown(f"**Timestamp:** `{step.timestamp}` | **Decision:** {step.decision}")
                st.code(step.details, language="text")
    else:
        st.info("Run a recipe generation from Tab 1 to inspect the live multi-agent execution trace and reflection audits.")
