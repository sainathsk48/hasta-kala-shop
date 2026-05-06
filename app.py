import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Hasta-Kala Shop", page_icon="🎨", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #FDF8F5; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; background-color: #C05C3E; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #E07A5F; border: none; color: white; }
    .metric-card { background-color: #C05C3E; color: white; padding: 20px; border-radius: 16px; margin-bottom: 20px; }
    .insight-card { background-color: #FFF9F2; border-left: 5px solid #F7B32B; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA INITIALIZATION ---
PRODUCTS = [
    {"name": "Banana Bag", "price": 450},
    {"name": "Keychain", "price": 80},
    {"name": "Handwoven Mat", "price": 1200},
    {"name": "Wooden Toy", "price": 250},
]
COLORS = ["Red", "Blue", "Green", "Natural"]

if 'sales' not in st.session_state:
    st.session_state.sales = []
if 'inventory' not in st.session_state:
    st.session_state.inventory = {f"{p['name']}-{c}": 10 for p in PRODUCTS for c in COLORS}

# --- FUNCTIONS ---
def add_sale(item, color, price):
    sku = f"{item}-{color}"
    if st.session_state.inventory.get(sku, 0) > 0:
        new_sale = {
            "id": datetime.now().timestamp(),
            "item": item,
            "color": color,
            "price": price,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.sales.append(new_sale)
        st.session_state.inventory[sku] -= 1
        return True
    return False

def reset_data():
    st.session_state.sales = []
    st.session_state.inventory = {f"{p['name']}-{c}": 10 for p in PRODUCTS for c in COLORS}
    st.rerun()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🎨 Hasta-Kala")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Dashboard", "Quick Bill", "Income Log", "Restock Inventory"])

if st.sidebar.button("🗑️ Reset All Data"):
    reset_data()

# --- DASHBOARD ---
if page == "Dashboard":
    st.title("Namaste, Artisan 👋")
    st.markdown("### Hasta-Kala Shop Dashboard")

    df = pd.DataFrame(st.session_state.sales)
    total_rev = df['price'].sum() if not df.empty else 0

    # --- GLOBAL STOCK ALERT ---
    stock_df = pd.DataFrame(st.session_state.inventory.items(), columns=['SKU', 'Stock'])
    low_stock = stock_df[stock_df['Stock'] <= 2]
    if not low_stock.empty:
        for _, row in low_stock.iterrows():
            st.error(f"🚨 **Stock Alert**: Only {row['Stock']} {row['SKU']} left — time to make more!")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <p style="opacity: 0.8; margin: 0;">Total Revenue</p>
                <h1 style="margin: 0; color: white;">₹{total_rev:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)

        if not df.empty:
            # Insights
            top_item = df['item'].value_counts().idxmax()
            item_pct = round((df['item'].value_counts().max() / len(df)) * 100)
            st.markdown(f"""
                <div class="insight-card">
                    <p style="font-weight: bold; margin: 0; color: #C05C3E;">Artisan Insight 💡</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.9em; color: #2D3047;">
                        Your <b>{top_item}s</b> are driving {item_pct}% of your total revenue. 
                        Consider increasing production of this item!
                    </p>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        if not df.empty:
            st.markdown("### Revenue Analysis")
            income_filter = st.selectbox("View by", ["Week", "Month", "Year"])
            
            df['date_obj'] = pd.to_datetime(df['date'])
            if income_filter == "Week":
                df['label'] = df['date_obj'].dt.strftime('%a')
            elif income_filter == "Month":
                df['label'] = "Week " + ((df['date_obj'].dt.day - 1) // 7 + 1).astype(str)
            else:
                df['label'] = df['date_obj'].dt.strftime('%b')

            bar_fig = px.bar(df.groupby('label')['price'].sum().reset_index(), 
                             x='label', y='price', 
                             color_discrete_sequence=['#E07A5F'],
                             template="plotly_white")
            bar_fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(bar_fig, use_container_width=True)

    st.markdown("---")
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### Best Selling Colors")
        if not df.empty:
            pie_fig = px.pie(df, names='color', 
                             color='color',
                             color_discrete_map={"Red": "#EF4444", "Blue": "#3B82F6", "Green": "#10B981", "Natural": "#D1B48C"},
                             template="plotly_white")
            pie_fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No sales yet. Go to 'Quick Bill' to log your first sale!")

    with col4:
        st.markdown("### Stock Inventory")
        if not low_stock.empty:
            st.info("Check the alerts at the top of the dashboard for specific items.")
        st.dataframe(stock_df.sort_values('Stock'), use_container_width=True)

# --- QUICK BILL ---
elif page == "Quick Bill":
    st.title("Quick Bill 💸")
    st.markdown("Log a new sale quickly.")

    col_p, col_c = st.columns(2)
    
    with col_p:
        st.markdown("#### 1. Select Product")
        selected_p_name = st.radio("Items", [p['name'] for p in PRODUCTS], horizontal=False)
        selected_p = next(p for p in PRODUCTS if p['name'] == selected_p_name)
    
    with col_c:
        st.markdown("#### 2. Select Color")
        selected_color = st.radio("Colors", COLORS, horizontal=True)

    st.markdown("---")
    if st.button(f"Complete Sale (₹{selected_p['price']})"):
        if add_sale(selected_p_name, selected_color, selected_p['price']):
            st.success(f"Successfully logged: {selected_color} {selected_p_name}")
            st.balloons()
        else:
            st.error(f"Out of stock for {selected_color} {selected_p_name}!")

# --- INCOME LOG ---
elif page == "Income Log":
    st.title("Income Log 📊")
    
    df = pd.DataFrame(st.session_state.sales)
    
    if not df.empty:
        filter_col = st.columns([1, 1, 1, 1])
        with filter_col[0]:
            log_filter = st.radio("Time Range", ["All", "This Week", "This Month"], horizontal=True)

        # Filtering logic
        df['date_obj'] = pd.to_datetime(df['date'])
        now = datetime.now()
        if log_filter == "This Week":
            df = df[df['date_obj'] > (now - timedelta(days=7))]
        elif log_filter == "This Month":
            df = df[df['date_obj'] > (now - timedelta(days=30))]

        st.markdown(f"#### Total for {log_filter}: **₹{df['price'].sum():,.2f}**")
        st.dataframe(df[['date', 'item', 'color', 'price']].sort_values('date', ascending=False), use_container_width=True)

        st.markdown("---")
        # Download Report
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Sales Report (CSV)",
            data=csv,
            file_name=f"Hasta-Kala-Report-{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime='text/csv',
        )
    else:
        st.info("No transactions found.")

# --- RESTOCK INVENTORY ---
elif page == "Restock Inventory":
    st.title("Restock Inventory 🛠️")
    st.markdown("Update your stock levels after producing new items.")

    col_p, col_c, col_q = st.columns([2, 1, 1])
    
    with col_p:
        st.markdown("#### 1. Select Product")
        p_name = st.selectbox("Product", [p['name'] for p in PRODUCTS])
    
    with col_c:
        st.markdown("#### 2. Color")
        c_name = st.selectbox("Color", COLORS)
    
    with col_q:
        st.markdown("#### 3. New Units")
        new_qty = st.number_input("Quantity Made", min_value=1, value=5)

    sku = f"{p_name}-{c_name}"
    current = st.session_state.inventory.get(sku, 0)
    
    st.info(f"Current Stock for {sku}: **{current}**")

    if st.button(f"Update {sku} Stock"):
        st.session_state.inventory[sku] = current + new_qty
        st.success(f"Added {new_qty} units! New total for {sku}: **{st.session_state.inventory[sku]}**")
        st.balloons()
