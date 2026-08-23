import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

st.set_page_config(
    page_title="PartnerFit",
    page_icon="💆",
    layout="wide"
)

# -----------------------------
# DEMO DATA
# -----------------------------

orders = pd.DataFrame([
    {
        "Order ID": "YM001",
        "Service": "Facial",
        "Customer Location": "Sector 62",
        "Order Date": "25 Aug 2026",
        "Order Time": "17:00",
        "Duration": 60,
        "Payout": 400,
        "Booking Type": "Advance"
    },
    {
        "Order ID": "YM002",
        "Service": "Waxing",
        "Customer Location": "Sector 45",
        "Order Date": "25 Aug 2026",
        "Order Time": "19:00",
        "Duration": 45,
        "Payout": 350,
        "Booking Type": "Immediate"
    }
])

partners = pd.DataFrame([
    {
        "Partner": "Priya Sharma",
        "Location": "Sector 63",
        "Services": "Facial, Waxing",
        "Available": "Yes",
        "Kit": "Yes",
        "Vehicle": "Scooter",
        "Travel Cost/km": 6,
        "Net Income Target": 350
    },
    {
        "Partner": "Ananya Verma",
        "Location": "Sector 45",
        "Services": "Facial, Manicure",
        "Available": "Yes",
        "Kit": "Yes",
        "Vehicle": "Metro",
        "Travel Cost/km": 3,
        "Net Income Target": 300
    },
    {
        "Partner": "Neha Singh",
        "Location": "Sector 76",
        "Services": "Facial, Waxing",
        "Available": "No",
        "Kit": "Yes",
        "Vehicle": "Bike",
        "Travel Cost/km": 5,
        "Net Income Target": 400
    }
])

# -----------------------------
# HEADER
# -----------------------------

st.title("💆 PartnerFit")
st.caption("Yes Madam — Partner Assignment Decision Prototype")

st.divider()

# -----------------------------
# ORDER SELECTION
# -----------------------------

st.subheader("1. Select Customer Order")

order_id = st.selectbox(
    "Select Order",
    orders["Order ID"]
)

order = orders[orders["Order ID"] == order_id].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Service", order["Service"])

with col2:
    st.metric("Duration", f'{order["Duration"]} min')

with col3:
    st.metric("Payout", f'₹{order["Payout"]}')

with col4:
    st.metric("Booking", order["Booking Type"])

st.info(
    f'Customer: {order["Customer Location"]}  |  '
    f'Date: {order["Order Date"]}  |  '
    f'Time: {order["Order Time"]}'
)

st.divider()

# -----------------------------
# PARTNER FILTER
# -----------------------------

st.subheader("2. Available Partners")

service_partners = partners[
    (partners["Available"] == "Yes") &
    (partners["Services"].str.contains(order["Service"], case=False))
].copy()

if len(service_partners) == 0:
    st.warning("No suitable partner available.")
else:

    # Simple demo travel estimates
    distance_map = {
        "Priya Sharma": 2.4,
        "Ananya Verma": 4.1,
        "Neha Singh": 6.2
    }

    eta_map = {
        "Priya Sharma": 12,
        "Ananya Verma": 22,
        "Neha Singh": 28
    }

    service_partners["Distance"] = service_partners["Partner"].map(distance_map)
    service_partners["ETA"] = service_partners["Partner"].map(eta_map)

    service_partners["Travel Cost"] = (
        service_partners["Distance"] *
        service_partners["Travel Cost/km"]
    ).round(0)

    service_partners["Net Income"] = (
        order["Payout"] -
        service_partners["Travel Cost"]
    ).round(0)

    # Simple operational score
    service_partners["Score"] = (
        100
        - service_partners["ETA"] * 1.5
        - service_partners["Distance"] * 3
    ).round(0)

    service_partners = service_partners.sort_values(
        "Score",
        ascending=False
    )

    # -----------------------------
    # PARTNER TABLE
    # -----------------------------

    display_df = service_partners[
        [
            "Partner",
            "Location",
            "Vehicle",
            "Distance",
            "ETA",
            "Travel Cost",
            "Net Income",
            "Score"
        ]
    ].copy()

    display_df.columns = [
        "Partner",
        "Location",
        "Vehicle",
        "Distance (km)",
        "ETA (min)",
        "Travel Cost (₹)",
        "Net Income (₹)",
        "Fit Score"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # -----------------------------
    # ASSIGNMENT
    # -----------------------------

    st.subheader("3. Recommended Assignment")

    best_partner = service_partners.iloc[0]

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Recommended Partner", best_partner["Partner"])

    with c2:
        st.metric("Distance", f'{best_partner["Distance"]} km')

    with c3:
        st.metric("ETA", f'{best_partner["ETA"]} min')

    with c4:
        st.metric("Net Income", f'₹{best_partner["Net Income"]}')

    if st.button(
        f'Assign Order to {best_partner["Partner"]}',
        type="primary"
    ):
        st.success(
            f'Order {order_id} assigned to '
            f'{best_partner["Partner"]}.'
        )

st.divider()

st.caption(
    "Prototype: decision-support logic using availability, service fit, "
    "travel distance, ETA, travel cost and partner economics."
)
