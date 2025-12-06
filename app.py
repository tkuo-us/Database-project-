"""
Weekly Grocery Management System - Streamlit Application
A comprehensive database-driven web application for managing weekly groceries.

Features:
- User authentication and registration
- Product and category management (CRUD operations)
- Shopping list creation and management
- Order processing and tracking
- Expense tracking and budget monitoring
- Visual analytics and reporting
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database as db

# Page configuration
st.set_page_config(
    page_title="Weekly Grocery Management System",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        border-radius: 5px;
        color: #155724;
    }
    .warning-message {
        padding: 1rem;
        background-color: #fff3cd;
        border-radius: 5px;
        color: #856404;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
db.init_database()

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_order_id' not in st.session_state:
    st.session_state.current_order_id = None

# ==================== AUTHENTICATION ====================

def show_login_page():
    """Display login/registration page"""
    st.markdown("<h1 class='main-header'>🛒 Weekly Grocery Management System</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.subheader("Welcome Back!")
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if username and password:
                        user = db.authenticate_user(username, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['user_id']
                            st.session_state.username = user['username']
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter username and password")
        
        with tab2:
            st.subheader("Create Account")
            with st.form("register_form"):
                new_username = st.text_input("Username", key="reg_username")
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                register = st.form_submit_button("Register", use_container_width=True)
                
                if register:
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.warning("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        try:
                            db.create_user(new_username, new_email, new_password)
                            st.success("Registration successful! Please login.")
                        except ValueError as e:
                            st.error(str(e))
        
        # Demo login option
        st.divider()
        st.info("🎯 **Demo Account**: Use `demo_user` / `password123` to explore the system")
        if st.button("Load Sample Data", use_container_width=True):
            db.insert_sample_data()
            st.success("Sample data loaded!")

# ==================== DASHBOARD ====================

def show_dashboard():
    """Display main dashboard with analytics"""
    st.markdown("## 📊 Dashboard")
    
    # Get user statistics
    spending = db.get_total_spending(st.session_state.user_id)
    total_spent = spending['total_spent'] if spending['total_spent'] else 0
    total_orders = spending['total_orders'] if spending['total_orders'] else 0
    
    # Get inventory summary
    inv_summary = db.get_inventory_summary(st.session_state.user_id)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Total Spent", f"${total_spent:.2f}")
    with col2:
        st.metric("📦 Total Orders", total_orders)
    with col3:
        avg_order = total_spent / total_orders if total_orders > 0 else 0
        st.metric("📈 Avg Order Value", f"${avg_order:.2f}")
    with col4:
        inventory_count = inv_summary['total_items'] if inv_summary and inv_summary['total_items'] else 0
        st.metric("🏠 Inventory Items", inventory_count)
    
    st.divider()
    
    # Alerts Section - Expiring, Low Stock, Out of Stock
    st.markdown("### ⚠️ Alerts & Notifications")
    
    alert_col1, alert_col2, alert_col3 = st.columns(3)
    
    # Items Expiring Soon (Within 7 Days)
    with alert_col1:
        expiring_items = db.get_expiring_soon(st.session_state.user_id, days=7)
        expired_items = db.get_expired_items(st.session_state.user_id)
        
        if expired_items:
            st.error(f"🚨 **{len(expired_items)} Expired Items**")
            for item in expired_items[:5]:
                days_exp = int(item['days_expired']) if item['days_expired'] else 0
                st.markdown(f"- ❌ **{item['product_name']}** - Expired {days_exp} days ago")
            if len(expired_items) > 5:
                st.caption(f"... and {len(expired_items) - 5} more")
        
        if expiring_items:
            st.warning(f"⏰ **{len(expiring_items)} Items Expiring Soon**")
            for item in expiring_items[:5]:
                days_left = int(item['days_until_expiry']) if item['days_until_expiry'] else 0
                if days_left == 0:
                    st.markdown(f"- 🔴 **{item['product_name']}** - Expires TODAY!")
                elif days_left == 1:
                    st.markdown(f"- 🟠 **{item['product_name']}** - Expires tomorrow")
                else:
                    st.markdown(f"- 🟡 **{item['product_name']}** - {days_left} days left")
            if len(expiring_items) > 5:
                st.caption(f"... and {len(expiring_items) - 5} more")
        
        if not expired_items and not expiring_items:
            st.success("✅ No items expiring soon!")
    
    # Low Stock Items
    with alert_col2:
        low_stock = db.get_low_stock_items(st.session_state.user_id)
        
        if low_stock:
            st.warning(f"📉 **{len(low_stock)} Items Running Low**")
            for item in low_stock[:5]:
                st.markdown(f"- **{item['product_name']}** - Only {item['quantity']} {item['unit_measure']} left")
            if len(low_stock) > 5:
                st.caption(f"... and {len(low_stock) - 5} more")
        else:
            st.success("✅ All items well stocked!")
    
    # Out of Stock Items
    with alert_col3:
        out_of_stock = db.get_out_of_stock_items(st.session_state.user_id)
        
        if out_of_stock:
            st.error(f"🚫 **{len(out_of_stock)} Items Out of Stock**")
            for item in out_of_stock[:5]:
                st.markdown(f"- **{item['product_name']}** ({item['brand']})")
            if len(out_of_stock) > 5:
                st.caption(f"... and {len(out_of_stock) - 5} more")
        else:
            st.success("✅ Nothing out of stock!")
    
    st.divider()
    
    # Current Inventory Overview
    st.markdown("### 🏠 Current Inventory Overview")
    
    inv_col1, inv_col2 = st.columns(2)
    
    with inv_col1:
        st.subheader("📍 Inventory by Location")
        inv_by_location = db.get_inventory_by_location(st.session_state.user_id)
        if inv_by_location:
            df = pd.DataFrame([dict(row) for row in inv_by_location])
            fig = px.pie(df, values='total_quantity', names='location',
                        hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data yet. Add items to your inventory!")
    
    with inv_col2:
        st.subheader("📦 Inventory by Category")
        inv_by_category = db.get_inventory_by_category(st.session_state.user_id)
        if inv_by_category:
            df = pd.DataFrame([dict(row) for row in inv_by_category])
            fig = px.bar(df, x='category_name', y='total_quantity',
                        color='item_count', text='total_quantity',
                        labels={'category_name': 'Category', 'total_quantity': 'Total Qty', 'item_count': 'Items'})
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data yet.")
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Spending by Category")
        category_spending = db.get_spending_by_category(st.session_state.user_id)
        if category_spending:
            df = pd.DataFrame([dict(row) for row in category_spending])
            fig = px.pie(df, values='total_spent', names='category_name', 
                        hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No spending data yet. Start shopping to see analytics!")
    
    with col2:
        st.subheader("📅 Monthly Spending Trend")
        monthly_spending = db.get_monthly_spending(st.session_state.user_id)
        if monthly_spending:
            df = pd.DataFrame([dict(row) for row in monthly_spending])
            fig = px.line(df, x='month', y='total_spent', markers=True,
                         labels={'month': 'Month', 'total_spent': 'Amount ($)'})
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No monthly data yet.")
    
    # Most purchased products
    st.subheader("🏆 Most Purchased Products")
    top_products = db.get_most_purchased_products(st.session_state.user_id, limit=5)
    if top_products:
        df = pd.DataFrame([dict(row) for row in top_products])
        fig = px.bar(df, x='product_name', y='total_quantity', 
                    color='category_name', text='total_quantity',
                    labels={'product_name': 'Product', 'total_quantity': 'Quantity'})
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No purchase history yet.")
    
    # Product suggestions
    st.subheader("💡 Suggested Products")
    suggestions = db.get_suggested_products(st.session_state.user_id, limit=5)
    if suggestions:
        cols = st.columns(5)
        for i, product in enumerate(suggestions):
            with cols[i % 5]:
                st.markdown(f"""
                **{product['product_name']}**  
                {product['brand']}  
                ${product['unit_price']:.2f}
                """)
    else:
        st.info("Shop more to get personalized suggestions!")

# ==================== PRODUCTS MANAGEMENT ====================

def show_products_page():
    """Display products management page"""
    st.markdown("## 📦 Product Management")
    
    tab1, tab2, tab3 = st.tabs(["🔍 Browse Products", "➕ Add Product", "📁 Categories"])
    
    with tab1:
        # Search and filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 Search products", placeholder="Search by name or brand...")
        with col2:
            categories = db.get_all_categories()
            category_options = ["All Categories"] + [c['category_name'] for c in categories]
            selected_category = st.selectbox("Filter by Category", category_options)
        
        # Get products
        if search:
            products = db.search_products(search)
        elif selected_category != "All Categories":
            cat = next((c for c in categories if c['category_name'] == selected_category), None)
            products = db.get_products_by_category(cat['category_id']) if cat else []
        else:
            products = db.get_all_products()
        
        # Display products in a table
        if products:
            df = pd.DataFrame([dict(row) for row in products])
            df = df[['product_id', 'product_name', 'brand', 'category_name', 'unit_price', 'unit_measure']]
            df.columns = ['ID', 'Product Name', 'Brand', 'Category', 'Price ($)', 'Unit']
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Edit/Delete product
            st.subheader("Edit Product")
            product_options = {f"{p['product_name']} - {p['brand']}": p['product_id'] for p in products}
            selected_product = st.selectbox("Select product to edit", list(product_options.keys()))
            
            if selected_product:
                product_id = product_options[selected_product]
                product = db.get_product_by_id(product_id)
                
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input("Product Name", value=product['product_name'])
                    edit_brand = st.text_input("Brand", value=product['brand'] or '')
                    edit_category = st.selectbox(
                        "Category", 
                        [c['category_id'] for c in categories],
                        format_func=lambda x: next(c['category_name'] for c in categories if c['category_id'] == x),
                        index=next(i for i, c in enumerate(categories) if c['category_id'] == product['category_id'])
                    )
                with col2:
                    edit_price = st.number_input("Unit Price ($)", value=float(product['unit_price']), min_value=0.01)
                    edit_unit = st.text_input("Unit Measure", value=product['unit_measure'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Update Product", use_container_width=True):
                        db.update_product(product_id, edit_name, edit_category, edit_price, edit_brand, edit_unit)
                        st.success("Product updated!")
                        st.rerun()
                with col2:
                    if st.button("🗑️ Delete Product", use_container_width=True, type="secondary"):
                        try:
                            db.delete_product(product_id)
                            st.success("Product deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cannot delete: {e}")
        else:
            st.info("No products found.")
    
    with tab2:
        st.subheader("Add New Product")
        categories = db.get_all_categories()
        
        if not categories:
            st.warning("Please create categories first!")
        else:
            with st.form("add_product_form"):
                col1, col2 = st.columns(2)
                with col1:
                    product_name = st.text_input("Product Name*")
                    brand = st.text_input("Brand")
                    category_id = st.selectbox(
                        "Category*",
                        [c['category_id'] for c in categories],
                        format_func=lambda x: next(c['category_name'] for c in categories if c['category_id'] == x)
                    )
                with col2:
                    unit_price = st.number_input("Unit Price ($)*", min_value=0.01, value=1.00)
                    unit_measure = st.text_input("Unit Measure", value="unit")
                
                if st.form_submit_button("➕ Add Product", use_container_width=True):
                    if product_name:
                        db.create_product(product_name, category_id, unit_price, brand, unit_measure)
                        st.success(f"Product '{product_name}' added successfully!")
                        st.rerun()
                    else:
                        st.warning("Product name is required!")
    
    with tab3:
        st.subheader("Manage Categories")
        
        # Display existing categories
        categories = db.get_all_categories()
        if categories:
            df = pd.DataFrame([dict(row) for row in categories])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Add new category
        st.subheader("Add New Category")
        with st.form("add_category_form"):
            cat_name = st.text_input("Category Name")
            cat_desc = st.text_area("Description (optional)")
            
            if st.form_submit_button("➕ Add Category"):
                if cat_name:
                    try:
                        db.create_category(cat_name, cat_desc)
                        st.success(f"Category '{cat_name}' added!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                else:
                    st.warning("Category name is required!")

# ==================== SHOPPING LISTS ====================

def show_shopping_lists_page():
    """Display shopping lists management page"""
    st.markdown("## 📝 Shopping Lists")
    
    col1, col2 = st.columns([2, 1])
    
    with col2:
        st.subheader("Create New List")
        with st.form("create_list_form"):
            list_name = st.text_input("List Name", placeholder="e.g., Weekly Groceries")
            if st.form_submit_button("➕ Create List", use_container_width=True):
                if list_name:
                    db.create_shopping_list(st.session_state.user_id, list_name)
                    st.success(f"List '{list_name}' created!")
                    st.rerun()
                else:
                    st.warning("Please enter a list name")
    
    with col1:
        st.subheader("Your Shopping Lists")
        lists = db.get_user_shopping_lists(st.session_state.user_id)
        
        if lists:
            for shopping_list in lists:
                status = "✅" if not shopping_list['is_active'] else "📝"
                with st.expander(f"{status} {shopping_list['list_name']} ({shopping_list['total_items'] or 0} items)"):
                    items = db.get_shopping_list_items(shopping_list['list_id'])
                    
                    if items:
                        # Calculate estimated total
                        total = sum(item['unit_price'] * item['quantity'] for item in items)
                        st.metric("Estimated Total", f"${total:.2f}")
                        
                        # Display items grouped by category
                        df = pd.DataFrame([dict(item) for item in items])
                        
                        for cat in df['category_name'].unique():
                            st.markdown(f"**{cat}**")
                            cat_items = df[df['category_name'] == cat]
                            for _, item in cat_items.iterrows():
                                col1, col2, col3 = st.columns([3, 1, 1])
                                with col1:
                                    checked = item['is_purchased'] == 1
                                    st.checkbox(
                                        f"{item['product_name']} ({item['brand']}) - {item['quantity']} {item['unit_measure']}",
                                        value=checked,
                                        key=f"item_{item['item_id']}",
                                        on_change=lambda id=item['item_id']: db.toggle_shopping_list_item(id)
                                    )
                                with col2:
                                    st.write(f"${item['unit_price'] * item['quantity']:.2f}")
                    else:
                        st.info("No items in this list yet")
                    
                    # Add items to list
                    if shopping_list['is_active']:
                        st.divider()
                        products = db.get_all_products()
                        product_options = {f"{p['product_name']} - {p['brand']} (${p['unit_price']})": p['product_id'] for p in products}
                        
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            selected = st.selectbox("Add product", list(product_options.keys()), key=f"add_{shopping_list['list_id']}")
                        with col2:
                            qty = st.number_input("Qty", min_value=1, value=1, key=f"qty_{shopping_list['list_id']}")
                        with col3:
                            if st.button("➕ Add", key=f"btn_{shopping_list['list_id']}"):
                                db.add_item_to_shopping_list(shopping_list['list_id'], product_options[selected], qty)
                                st.rerun()
                        
                        # Actions
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🛒 Convert to Order", key=f"convert_{shopping_list['list_id']}", use_container_width=True):
                                try:
                                    order_id = db.convert_shopping_list_to_order(shopping_list['list_id'], st.session_state.user_id)
                                    st.success(f"Order #{order_id} created!")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))
                        with col2:
                            if st.button("🗑️ Delete List", key=f"del_{shopping_list['list_id']}", use_container_width=True, type="secondary"):
                                db.delete_shopping_list(shopping_list['list_id'])
                                st.rerun()
        else:
            st.info("No shopping lists yet. Create one to get started!")

# ==================== ORDERS ====================

def show_orders_page():
    """Display orders management page"""
    st.markdown("## 🛒 Orders")
    
    tab1, tab2 = st.tabs(["📋 Order History", "➕ New Order"])
    
    with tab1:
        orders = db.get_user_orders(st.session_state.user_id)
        
        if orders:
            for order in orders:
                status_icon = "✅" if order['status'] == 'completed' else "⏳"
                order_date = datetime.fromisoformat(order['order_date']) if order['order_date'] else datetime.now()
                
                with st.expander(f"{status_icon} Order #{order['order_id']} - {order_date.strftime('%Y-%m-%d %H:%M')} - ${order['total_amount']:.2f}"):
                    details = db.get_order_details(order['order_id'])
                    
                    if details:
                        df = pd.DataFrame([dict(d) for d in details])
                        df = df[['product_name', 'brand', 'category_name', 'quantity', 'unit_price', 'subtotal']]
                        df.columns = ['Product', 'Brand', 'Category', 'Qty', 'Unit Price ($)', 'Subtotal ($)']
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        st.markdown(f"**Total: ${order['total_amount']:.2f}**")
                    
                    if order['status'] == 'pending':
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Complete Order", key=f"complete_{order['order_id']}", use_container_width=True):
                                db.complete_order(order['order_id'])
                                st.success("Order completed!")
                                st.rerun()
                        with col2:
                            if st.button("🗑️ Cancel Order", key=f"cancel_{order['order_id']}", use_container_width=True, type="secondary"):
                                db.delete_order(order['order_id'])
                                st.rerun()
        else:
            st.info("No orders yet. Create a shopping list and convert it to an order!")
    
    with tab2:
        st.subheader("Create New Order")
        
        # Initialize or get current order
        if st.session_state.current_order_id is None:
            if st.button("🆕 Start New Order", use_container_width=True):
                st.session_state.current_order_id = db.create_order(st.session_state.user_id)
                st.rerun()
        else:
            order = db.get_order_by_id(st.session_state.current_order_id)
            st.info(f"Current Order #{st.session_state.current_order_id} - Total: ${order['total_amount']:.2f}")
            
            # Current items
            details = db.get_order_details(st.session_state.current_order_id)
            if details:
                st.subheader("Order Items")
                df = pd.DataFrame([dict(d) for d in details])
                df = df[['product_name', 'brand', 'quantity', 'unit_price', 'subtotal']]
                df.columns = ['Product', 'Brand', 'Qty', 'Unit Price', 'Subtotal']
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Add items
            st.subheader("Add Items")
            products = db.get_all_products()
            product_options = {f"{p['product_name']} - {p['brand']} (${p['unit_price']})": p['product_id'] for p in products}
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                selected_product = st.selectbox("Select Product", list(product_options.keys()))
            with col2:
                quantity = st.number_input("Quantity", min_value=1, value=1)
            with col3:
                if st.button("➕ Add to Order", use_container_width=True):
                    db.add_order_detail(st.session_state.current_order_id, product_options[selected_product], quantity)
                    st.rerun()
            
            # Actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Complete Order", use_container_width=True, type="primary"):
                    db.complete_order(st.session_state.current_order_id)
                    st.session_state.current_order_id = None
                    st.success("Order completed!")
                    st.rerun()
            with col2:
                if st.button("🗑️ Cancel Order", use_container_width=True, type="secondary"):
                    db.delete_order(st.session_state.current_order_id)
                    st.session_state.current_order_id = None
                    st.rerun()

# ==================== REPORTS ====================

def show_reports_page():
    """Display reports and analytics page"""
    st.markdown("## 📈 Reports & Analytics")
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    st.divider()
    
    # Category spending breakdown
    st.subheader("💰 Spending by Category")
    category_data = db.get_spending_by_category(
        st.session_state.user_id,
        start_date.isoformat(),
        end_date.isoformat()
    )
    
    if category_data:
        df = pd.DataFrame([dict(row) for row in category_data])
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df, values='total_spent', names='category_name',
                        title='Spending Distribution', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df, x='category_name', y='total_spent',
                        title='Spending by Category',
                        labels={'category_name': 'Category', 'total_spent': 'Amount ($)'})
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No spending data for the selected period.")
    
    # Monthly trends
    st.subheader("📅 Monthly Spending Trends")
    monthly_data = db.get_monthly_spending(st.session_state.user_id)
    
    if monthly_data:
        df = pd.DataFrame([dict(row) for row in monthly_data])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['month'], y=df['total_spent'],
            mode='lines+markers', name='Total Spent',
            line=dict(color='#1E88E5', width=3)
        ))
        fig.add_trace(go.Bar(
            x=df['month'], y=df['order_count'],
            name='Order Count', yaxis='y2',
            opacity=0.5
        ))
        fig.update_layout(
            title='Monthly Spending and Order Count',
            yaxis=dict(title='Amount ($)'),
            yaxis2=dict(title='Orders', overlaying='y', side='right'),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No monthly data available.")
    
    # Top products
    st.subheader("🏆 Top 10 Most Purchased Products")
    top_products = db.get_most_purchased_products(st.session_state.user_id, limit=10)
    
    if top_products:
        df = pd.DataFrame([dict(row) for row in top_products])
        df = df[['product_name', 'brand', 'category_name', 'total_quantity', 'order_count']]
        df.columns = ['Product', 'Brand', 'Category', 'Total Qty', 'Times Ordered']
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No purchase data available.")
    
    # Weekly spending summary
    st.subheader("📊 Last 7 Days")
    weekly_data = db.get_weekly_spending(st.session_state.user_id)
    
    if weekly_data:
        df = pd.DataFrame([dict(row) for row in weekly_data])
        fig = px.bar(df, x='day', y='daily_total',
                    title='Daily Spending (Last 7 Days)',
                    labels={'day': 'Date', 'daily_total': 'Amount ($)'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for the last 7 days.")

# ==================== INVENTORY MANAGEMENT ====================

def show_inventory_page():
    """Display inventory management page"""
    st.markdown("## 🏠 Inventory Management")
    
    tab1, tab2, tab3 = st.tabs(["📦 Current Inventory", "➕ Add to Inventory", "⚠️ Alerts"])
    
    with tab1:
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("🔍 Search inventory", placeholder="Search by product name...")
        with col2:
            location_filter = st.selectbox("Filter by Location", 
                ["All Locations", "Pantry", "Refrigerator", "Freezer", "Cabinet", "Other"])
        
        # Get inventory
        inventory = db.get_user_inventory(st.session_state.user_id)
        
        if inventory:
            # Apply filters
            filtered_inv = [dict(item) for item in inventory]
            if search:
                filtered_inv = [i for i in filtered_inv if search.lower() in i['product_name'].lower()]
            if location_filter != "All Locations":
                filtered_inv = [i for i in filtered_inv if i['location'] == location_filter]
            
            if filtered_inv:
                # Display as table
                df = pd.DataFrame(filtered_inv)
                display_cols = ['product_name', 'brand', 'category_name', 'quantity', 'unit_measure', 
                               'min_quantity', 'expiry_date', 'location']
                df_display = df[display_cols].copy()
                df_display.columns = ['Product', 'Brand', 'Category', 'Qty', 'Unit', 'Min Qty', 'Expiry', 'Location']
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Edit inventory item
                st.subheader("Edit Inventory Item")
                inv_options = {f"{i['product_name']} ({i['location']})": i['inventory_id'] for i in filtered_inv}
                selected_inv = st.selectbox("Select item to edit", list(inv_options.keys()))
                
                if selected_inv:
                    inv_id = inv_options[selected_inv]
                    item = next(i for i in filtered_inv if i['inventory_id'] == inv_id)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_qty = st.number_input("Quantity", value=item['quantity'], min_value=0)
                        new_min = st.number_input("Min Quantity", value=item['min_quantity'] or 2, min_value=0)
                    with col2:
                        new_expiry = st.date_input("Expiry Date", 
                            value=datetime.strptime(item['expiry_date'], '%Y-%m-%d').date() if item['expiry_date'] else None)
                        new_location = st.selectbox("Location", 
                            ["Pantry", "Refrigerator", "Freezer", "Cabinet", "Other"],
                            index=["Pantry", "Refrigerator", "Freezer", "Cabinet", "Other"].index(item['location']) if item['location'] in ["Pantry", "Refrigerator", "Freezer", "Cabinet", "Other"] else 0)
                    with col3:
                        new_notes = st.text_area("Notes", value=item['notes'] or '')
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Update Item", use_container_width=True):
                            db.update_inventory_item(inv_id, new_qty, new_min, 
                                new_expiry.isoformat() if new_expiry else None, new_location, new_notes)
                            st.success("Item updated!")
                            st.rerun()
                    with col2:
                        use_qty = st.number_input("Use quantity", min_value=1, value=1, key="use_qty")
                    with col3:
                        if st.button("📉 Use Item", use_container_width=True):
                            db.use_inventory_item(inv_id, use_qty)
                            st.success(f"Used {use_qty} {item['unit_measure']}!")
                            st.rerun()
                    
                    if st.button("🗑️ Remove from Inventory", type="secondary"):
                        db.delete_inventory_item(inv_id)
                        st.success("Item removed!")
                        st.rerun()
            else:
                st.info("No items match your search/filter.")
        else:
            st.info("Your inventory is empty. Add items to start tracking!")
    
    with tab2:
        st.subheader("Add Item to Inventory")
        
        products = db.get_all_products()
        if products:
            with st.form("add_inventory_form"):
                col1, col2 = st.columns(2)
                with col1:
                    product_options = {f"{p['product_name']} - {p['brand']}": p['product_id'] for p in products}
                    selected_product = st.selectbox("Select Product", list(product_options.keys()))
                    quantity = st.number_input("Quantity", min_value=1, value=1)
                    min_quantity = st.number_input("Minimum Quantity (for low stock alerts)", min_value=0, value=2)
                with col2:
                    expiry_date = st.date_input("Expiry Date (optional)", value=None)
                    location = st.selectbox("Storage Location", 
                        ["Pantry", "Refrigerator", "Freezer", "Cabinet", "Other"])
                    notes = st.text_input("Notes (optional)")
                
                if st.form_submit_button("➕ Add to Inventory", use_container_width=True):
                    product_id = product_options[selected_product]
                    db.add_to_inventory(
                        st.session_state.user_id, 
                        product_id, 
                        quantity,
                        expiry_date.isoformat() if expiry_date else None,
                        location,
                        min_quantity,
                        notes
                    )
                    st.success(f"Added {quantity} x {selected_product.split(' - ')[0]} to inventory!")
                    st.rerun()
        else:
            st.warning("No products available. Please add products first!")
    
    with tab3:
        st.subheader("⚠️ Inventory Alerts")
        
        # Summary metrics
        inv_summary = db.get_inventory_summary(st.session_state.user_id)
        if inv_summary:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⏰ Expiring Soon", inv_summary['expiring_soon_count'] or 0)
            with col2:
                st.metric("❌ Expired", inv_summary['expired_count'] or 0)
            with col3:
                st.metric("📉 Low Stock", inv_summary['low_stock_count'] or 0)
            with col4:
                st.metric("🚫 Out of Stock", inv_summary['out_of_stock_count'] or 0)
        
        st.divider()
        
        # Expired Items
        st.markdown("### ❌ Expired Items")
        expired = db.get_expired_items(st.session_state.user_id)
        if expired:
            df = pd.DataFrame([dict(i) for i in expired])
            df['days_expired'] = df['days_expired'].astype(int)
            df_display = df[['product_name', 'brand', 'quantity', 'unit_measure', 'expiry_date', 'days_expired', 'location']]
            df_display.columns = ['Product', 'Brand', 'Qty', 'Unit', 'Expiry Date', 'Days Expired', 'Location']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.success("No expired items! 🎉")
        
        # Expiring Soon
        st.markdown("### ⏰ Expiring Within 7 Days")
        expiring = db.get_expiring_soon(st.session_state.user_id, days=7)
        if expiring:
            df = pd.DataFrame([dict(i) for i in expiring])
            df['days_until_expiry'] = df['days_until_expiry'].astype(int)
            df_display = df[['product_name', 'brand', 'quantity', 'unit_measure', 'expiry_date', 'days_until_expiry', 'location']]
            df_display.columns = ['Product', 'Brand', 'Qty', 'Unit', 'Expiry Date', 'Days Left', 'Location']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.success("No items expiring soon! 🎉")
        
        # Low Stock
        st.markdown("### 📉 Low Stock Items")
        low_stock = db.get_low_stock_items(st.session_state.user_id)
        if low_stock:
            df = pd.DataFrame([dict(i) for i in low_stock])
            df_display = df[['product_name', 'brand', 'quantity', 'min_quantity', 'unit_measure', 'location']]
            df_display.columns = ['Product', 'Brand', 'Current Qty', 'Min Qty', 'Unit', 'Location']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Quick add to shopping list
            if st.button("📝 Add All Low Stock Items to Shopping List"):
                lists = db.get_user_shopping_lists(st.session_state.user_id)
                active_lists = [l for l in lists if l['is_active']]
                if active_lists:
                    for item in low_stock:
                        db.add_item_to_shopping_list(active_lists[0]['list_id'], item['product_id'], item['min_quantity'] - item['quantity'] + 1)
                    st.success(f"Added {len(low_stock)} items to '{active_lists[0]['list_name']}'!")
                else:
                    list_id = db.create_shopping_list(st.session_state.user_id, "Restock List")
                    for item in low_stock:
                        db.add_item_to_shopping_list(list_id, item['product_id'], item['min_quantity'] - item['quantity'] + 1)
                    st.success(f"Created 'Restock List' with {len(low_stock)} items!")
                st.rerun()
        else:
            st.success("All items are well stocked! 🎉")
        
        # Out of Stock
        st.markdown("### 🚫 Out of Stock Items")
        out_of_stock = db.get_out_of_stock_items(st.session_state.user_id)
        if out_of_stock:
            df = pd.DataFrame([dict(i) for i in out_of_stock])
            df_display = df[['product_name', 'brand', 'category_name', 'unit_price']]
            df_display.columns = ['Product', 'Brand', 'Category', 'Price ($)']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.success("Nothing is out of stock! 🎉")

# ==================== MAIN APPLICATION ====================

def main():
    """Main application logic"""
    if not st.session_state.logged_in:
        show_login_page()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"### 👤 Welcome, {st.session_state.username}!")
            st.divider()
            
            menu = st.radio(
                "Navigation",
                ["📊 Dashboard", "📦 Products", "🏠 Inventory", "📝 Shopping Lists", "🛒 Orders", "📈 Reports"],
                label_visibility="collapsed"
            )
            
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.current_order_id = None
                st.rerun()
        
        # Main content area
        if menu == "📊 Dashboard":
            show_dashboard()
        elif menu == "📦 Products":
            show_products_page()
        elif menu == "🏠 Inventory":
            show_inventory_page()
        elif menu == "📝 Shopping Lists":
            show_shopping_lists_page()
        elif menu == "🛒 Orders":
            show_orders_page()
        elif menu == "📈 Reports":
            show_reports_page()

if __name__ == "__main__":
    main()