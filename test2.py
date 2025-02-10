import streamlit as st
import openai
import json
import random

# ---------------------------
# 1. 全局配置
# ---------------------------
openai.api_key = "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"

# 初始化 session_state 存储
if "page" not in st.session_state:
    st.session_state.page = "home"  # 默认首页
if "food_inventory" not in st.session_state:
    st.session_state.food_inventory = {}  # 仓库: {食材名: 数量}
if "preferences" not in st.session_state:
    st.session_state.preferences = ""      # 用户口味偏好
if "recipes_list" not in st.session_state:
    st.session_state.recipes_list = []     # 已生成的食谱列表（存放解析后的内容）


# ---------------------------
# 2. 布局：顶部和按钮
# ---------------------------
# 我们用一个三列布局，让右上角放“编辑口味”按钮，中间显示标题，下方放两个按钮“仓库”“生成食谱”
top_col1, top_col2, top_col3 = st.columns([4, 12, 3])

with top_col1:
    st.write("")  # 占位

with top_col2:
    st.title("What's for dinner?")

with top_col3:
    # 右上角按钮：编辑口味
    if st.button("Preference", key="edit_pref"):
        st.session_state.page = "preferences"

# 在标题下方放两个按钮：仓库 & 生成食谱
col1, col2 = st.columns([6, 1])  # 调整列的宽度比例，使按钮之间的距离更远
with col1:
    if st.button("Fridge", key="to_warehouse"):
        st.session_state.page = "warehouse"

with col2:
    if st.button("Recipes", key="to_recipes"):
        st.session_state.page = "recipes"



# ---------------------------
# 3. 函数：解析 AI 返回的 JSON
# ---------------------------
def parse_recipes_from_json(json_str):
    """
    解析AI返回的JSON格式字符串，获取食谱列表
    期望格式：
    {
      "recipes": [
        {
          "name": "Recipe Name",
          "description": "Short Description "
        },
        ...
      ]
    }
    """
    recipes = []
    try:
        data = json.loads(json_str)
        if "recipes" in data:
            recipes = data["recipes"]
    except json.JSONDecodeError:
        # 如果解析失败，可能AI输出不符合JSON格式，直接返回空
        pass
    return recipes


# ---------------------------
# 4. 函数：生成食谱名称列表
# ---------------------------
def generate_recipes_list(ingredients, preferences, n=5):
    """
    向 OpenAI 发送请求，让其基于食材和口味偏好
    返回一个JSON结构，包含 n 个菜名 + 简要描述
    """
    # 更详细的 prompt，要求返回 JSON 结构
    prompt = f"""
You are a professional chef, and the user has provided these ingredients: {", ".join(ingredients)}.
The user's taste preferences: {preferences if preferences else "No special preferences"}.
Please list {n} delicious dishes that can be made with the above ingredients.
Only return data in JSON format, like the example below:
{{
  "recipes": [
    {{"name": "Recipe1", "description": "Short description"}},
    {{"name": "Recipe2", "description": "Short description"}}
  ]
}}
Do not output any extra text.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional western food chef who needs to return a list of recipes in JSON format based on the user's preferences and ingredients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"


# ---------------------------
# 5. 函数：生成某个菜的详细做法
# ---------------------------
def generate_recipe_instructions(recipe_name, ingredients, preferences):
    """
    对具体的菜名，再次询问AI，生成详细的制作步骤
    """
    prompt = f"""
You are a professional chef. The user has these ingredients: {", ".join(ingredients)}.
The user wants to make: {recipe_name}.
The user's taste preferences: {preferences if preferences else "No special preferences"}.
Please list the detailed steps and techniques to make this dish.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional western food chef who needs to give detailed recipe instructions based on user preferences and ingredients。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"ERROR: {str(e)}"


# ---------------------------
# 6. 页面逻辑：根据 page 显示
# ---------------------------
def show_home_page():
    st.write("This is the homepage. You can click the buttons above to go to Warehouse, Generate Recipes, or Edit Preferences.")

def show_warehouse_page():
    st.subheader("🍖 My little fridge")
    
    # 增加仓库容量进度条（游戏化元素）
    total_items = sum(st.session_state.food_inventory.values())
    st.progress(min(total_items/50, 1), text=f"capacity: {total_items}/50")

    # 使用columns优化布局
    if st.session_state.food_inventory:
        for food, qty in st.session_state.food_inventory.items():
            # 使用3列布局：食材名 + 数量 + 操作按钮
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # 随机食材emoji映射
                food_emoji = {
                    "egg": "🥚", "beef": "🥩", "milk": "🥛", 
                    "tomato": "🍅", "rice": "🍚"
                }.get(food, "🌱")
                st.markdown(f"{food_emoji} **{food}**")

            with col2:
                st.markdown(f"`{qty}pcs`")
            
            # 更醒目的操作按钮
            with col3:
                if st.button(f"➕", key=f"plus_{food}", 
                           help="Increase quantity"):
                    st.session_state.food_inventory[food] += 1
                    st.rerun()
            
            with col4:
                if st.button(f"➖", key=f"minus_{food}",
                           help="Decrease quantity"):
                    st.session_state.food_inventory[food] -= 1
                    if st.session_state.food_inventory[food] <= 0:
                        del st.session_state.food_inventory[food]
                    st.rerun()
        
        st.markdown("---")
    else:
        st.markdown("> 🧺 The fridge is empty, add ingredients now!")

# 添加食材部分美化
with st.expander("✨ Add New Ingredient", expanded=True):
    new_food = st.text_input("Ingredient", key="new_food",
                           placeholder="e.g. Beef")
    new_qty = st.number_input("Quantity", min_value=1, value=1, format="%d")  
    
    if st.button("✨ Add to fridge！", type="primary"): 
        if new_food.strip():
            # Ensure food_inventory exists in session state
            if "food_inventory" not in st.session_state:
                st.session_state.food_inventory = {}

            # Update the inventory
            st.session_state.food_inventory[new_food.strip()] = st.session_state.food_inventory.get(new_food.strip(), 0) + new_qty
            
            # Display a success message
            st.success(f"🎉 Successfully added{new_food} x {new_qty}")
            
            # Rerun the app to reflect changes (if needed)
            st.rerun()



def show_preferences_page():
    st.subheader("👅 Taste Preferences")
    
    # ---- 新增部分：快捷选择按钮 ----
    st.markdown("**Quick Select：**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌶️ Spicy Food Lover", help="Loves spicy food", use_container_width=True):
            st.session_state.preferences += " Likes spicy food"
    with col2:
        if st.button("🍭 Dessert Lover", help="Loves sweets", use_container_width=True):
            st.session_state.preferences += " Likes sweets"
    with col3:
        if st.button("🍃 Healthy Light Meals", help="Low oil and salt", use_container_width=True):
            st.session_state.preferences += " Low oil and salt"
    
    # ---- 修改文本输入框 ----
    pref = st.text_area(
        "Write your personal taste preferences：",
        value=st.session_state.preferences,
        height=150,
        placeholder="e.g. \n- Dislike cilantro\n- Love cheese pull effect\n- Allergic to seafood"
    )
    
    # ---- 修改保存按钮 ----
    if st.button("🔒 save Preferences", type="primary"):
        st.session_state.preferences = pref
        st.success("✅ Taste preferences saved！")
        st.session_state.page = "home"
        st.rerun() 
def show_recipes_page():
    # 添加自定义 CSS（确保内容宽度）
    st.markdown("""
        <style>
        /* 覆盖 Streamlit 默认宽度 */
        div.stMarkdown > div > div > div > div > div {
            max-width: 100% !important;
            width: 90% !important;
        }
        /* 调整文本样式 */
        .custom-recipe-text {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            font-size: 16px !important;
            line-height: 1.6 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.subheader("🔮 Magic Recipe Generation")
    
    # 显示当前口味偏好
    pref_emoji = "🌶️" if "spicy" in st.session_state.preferences else "🍭"
    st.markdown(f"Current taste preferences：{pref_emoji} `{st.session_state.preferences or 'None'}`")

    # 食材选择部分
    selected_ingredients = []
    cols = st.columns(3)
    for idx, food in enumerate(st.session_state.food_inventory.keys()):
        with cols[idx % 3]:
            if st.checkbox(f"{food}", key=f"select_{food}"):
                selected_ingredients.append(food)
    
    # 生成食谱按钮
    if st.button("✨ Generate Recipe", type="primary", use_container_width=True):
        if not selected_ingredients:
            st.warning("⚠️ Please select at least one ingredient！")
        else:
            with st.spinner("🧙‍♂️ AI is generating your recipe..."):
                raw_json = generate_recipes_list(selected_ingredients, st.session_state.preferences, 5)
                if raw_json.startswith("ERROR:"):
                    st.error(raw_json)
                else:
                    new_recipes = parse_recipes_from_json(raw_json)
                    if new_recipes:
                        st.session_state.recipes_list.extend(new_recipes)
                        st.balloons()
                    else:
                        st.error("AI returned an unparseable format. Please try again later.")

    # 显示已生成的食谱
    st.write("### Generated Recipes")
    if st.session_state.recipes_list:
        for idx, r in enumerate(st.session_state.recipes_list):
            recipe_name = r.get("name", f"Untitled Recipe {idx+1}")
            desc = r.get("description", "")
            
            # 使用 st.expander 包裹菜品名称和做法
            with st.expander(f"**{idx+1}. {recipe_name}**  \n*{desc}*", expanded=False):
                # 动态生成做法内容
                instructions = generate_recipe_instructions(recipe_name, selected_ingredients, st.session_state.preferences)
                st.markdown(
                    f"""
                    <div class="custom-recipe-text">
                        {instructions}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.write("No recipes generated yet")

  
# ---------------------------
# 7. 显示不同页面
# ---------------------------
if st.session_state.page == "home":
    show_home_page()
elif st.session_state.page == "warehouse":
    show_warehouse_page()
elif st.session_state.page == "preferences":
    show_preferences_page()
elif st.session_state.page == "recipes":
    show_recipes_page()
