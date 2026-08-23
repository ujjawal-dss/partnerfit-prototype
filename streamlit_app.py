import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="PartnerFit",
    page_icon="🧑‍🔧",
    layout="wide"
)

SHEET_ID = "1yhe5-y05lVxroIqqBrXQG5_VfSA73G1ZZDCQEXwL5BY"

PARTNERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Partners"
SERVICES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Service"
ORDERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Orders"
WORKLOAD_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Workload"
TRAVEL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Travel"

@st.cache_data(ttl=60)
def load_data():
    partners = pd.read_csv(PARTNERS_URL)
    services = pd.read_csv(SERVICES_URL)
    orders = pd.read_csv(ORDERS_URL)
    workload = pd.read_csv(WORKLOAD_URL)
    travel = pd.read_csv(TRAVEL_URL)

    return partners, services, orders, workload, travel

st.title("PartnerFit")
st.caption("Yes Madam Partner Assignment Prototype")

try:
    partners, services, orders, workload, travel = load_data()

    st.success("Google Sheet connected successfully.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Partners", "Services", "Orders", "Workload", "Travel"]
)

    with tab1:
        st.subheader("Partners")
        st.dataframe(partners, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Services")
        st.dataframe(services, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Orders")
        st.dataframe(orders, use_container_width=True, hide_index=True)

    with tab4:
        st.subheader("Workload")
        st.dataframe(
            workload,
            use_container_width=True,
            hide_index=True
        )

    with tab5:
        st.subheader("Travel")
        st.dataframe(
            travel,
            use_container_width=True,
            hide_index=True
        )
    

except Exception as e:
    st.error("Could not load Google Sheet data.")
    st.code(str(e))
# ==========================================
# PARTNERFIT - ELIGIBILITY ENGINE
# ==========================================

st.divider()
st.subheader("🔍 Partner Eligibility Check")

# Clean column names
partners.columns = partners.columns.str.strip()
services.columns = services.columns.str.strip()
orders.columns = orders.columns.str.strip()


# Helper function to find matching column names
def find_column(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None


# Identify actual columns from Google Sheet
order_id_col = find_column(orders, ["Order ID", "OrderID"])
order_service_col = find_column(orders, ["Service", "Service Name"])

service_name_col = find_column(
    services,
    ["Service Name", "Service"]
)

required_skill_col = find_column(
    services,
    ["Required Skill", "Skill"]
)

required_kit_col = find_column(
    services,
    ["Required Kit", "Kit"]
)

partner_name_col = find_column(
    partners,
    ["Partner Name", "Name"]
)

active_col = find_column(
    partners,
    ["Active Status", "Active"]
)

skills_col = find_column(
    partners,
    ["Skills", "Skill"]
)

kit_col = find_column(
    partners,
    ["Kit Status", "Kit"]
)


# Stop safely if an important column is missing
required_columns = {
    "Order ID": order_id_col,
    "Order Service": order_service_col,
    "Service Name": service_name_col,
    "Required Skill": required_skill_col,
    "Required Kit": required_kit_col,
    "Partner Name": partner_name_col,
    "Active": active_col,
    "Skills": skills_col,
    "Kit Status": kit_col
}

missing = [
    name
    for name, column in required_columns.items()
    if column is None
]

if missing:
    st.error(
        "Missing columns: " + ", ".join(missing)
    )

    st.write("Orders columns:", list(orders.columns))
    st.write("Services columns:", list(services.columns))
    st.write("Partners columns:", list(partners.columns))

    st.stop()


# Select customer order
selected_order_id = st.selectbox(
    "Select Customer Order",
    orders[order_id_col].astype(str).tolist()
)

selected_order = orders[
    orders[order_id_col].astype(str)
    == selected_order_id
].iloc[0]

selected_service = str(
    selected_order[order_service_col]
).strip()

st.write("### Selected Order")

col1, col2 = st.columns(2)

with col1:
    st.write("**Order ID:**", selected_order_id)

with col2:
    st.write("**Service:**", selected_service)


# Find service requirements
matching_service = services[
    services[service_name_col]
    .astype(str)
    .str.strip()
    .str.lower()
    == selected_service.lower()
]

if matching_service.empty:
    st.error(
        f"No service configuration found for {selected_service}"
    )
    st.stop()

service_row = matching_service.iloc[0]

required_skill = str(
    service_row[required_skill_col]
).strip()

required_kit = str(
    service_row[required_kit_col]
).strip()

st.info(
    f"Required Skill: {required_skill} | "
    f"Required Kit: {required_kit}"
)


# Evaluate partners
results = []

for _, partner in partners.iterrows():

    # 1. Active status
    active_value = str(
        partner[active_col]
    ).strip().lower()

    active_ok = active_value in [
        "yes",
        "true",
        "1",
        "active"
    ]


    # 2. Skill match
    partner_skills = str(
        partner[skills_col]
    ).strip().lower()

    skill_ok = (
        required_skill.lower()
        in partner_skills
    )


    # 3. Kit check
    partner_kit = str(
        partner[kit_col]
    ).strip().lower()

    required_kit_clean = (
        required_kit
        .lower()
        .replace(" kit", "")
        .strip()
    )

    kit_ok = (
        required_kit_clean in partner_kit
        or partner_kit in [
            "available",
            "yes",
            "ready"
        ]
    )


    # Final eligibility
    eligible = (
        active_ok
        and skill_ok
        and kit_ok
    )

    results.append({
        "Partner": partner[partner_name_col],
        "Active": "✅" if active_ok else "❌",
        "Skill Match": "✅" if skill_ok else "❌",
        "Kit Ready": "✅" if kit_ok else "❌",
        "Eligible": "✅ YES" if eligible else "❌ NO"
    })


eligibility_df = pd.DataFrame(results)

st.write("### Eligibility Result")

st.dataframe(
    eligibility_df,
    use_container_width=True,
    hide_index=True
)


eligible_partners = eligibility_df[
    eligibility_df["Eligible"] == "✅ YES"
]

if len(eligible_partners) > 0:

    st.success(
        f"{len(eligible_partners)} partner(s) "
        f"eligible for this order."
    )

else:

    st.warning(
        "No partner currently satisfies "
        "the basic eligibility conditions."
    )

# ==========================================
# ELIGIBLE PARTNERS - OPERATIONAL COMPARISON
# ==========================================

st.divider()
st.subheader("📊 Eligible Partner Operational Comparison")

# Clean additional sheet column names
workload.columns = workload.columns.str.strip()
travel.columns = travel.columns.str.strip()

# Find partner ID column
partner_id_col = find_column(
    partners,
    ["Partner ID", "PartnerID"]
)

workload_partner_id_col = find_column(
    workload,
    ["Partner ID", "PartnerID"]
)

travel_partner_id_col = find_column(
    travel,
    ["Partner ID", "PartnerID"]
)

travel_order_id_col = find_column(
    travel,
    ["Order ID", "OrderID"]
)

if (
    partner_id_col is None
    or workload_partner_id_col is None
    or travel_partner_id_col is None
    or travel_order_id_col is None
):
    st.error("Partner ID / Order ID columns missing in Workload or Travel sheet.")
    st.stop()


# Create list of eligible partner names
eligible_names = eligibility_df[
    eligibility_df["Eligible"] == "✅ YES"
]["Partner"].tolist()


# Get eligible partner master records
eligible_master = partners[
    partners[partner_name_col].isin(eligible_names)
].copy()


# Filter travel only for selected order
selected_travel = travel[
    travel[travel_order_id_col].astype(str)
    == str(selected_order_id)
].copy()


# Merge partner + workload
comparison = eligible_master.merge(
    workload,
    left_on=partner_id_col,
    right_on=workload_partner_id_col,
    how="left"
)


# Merge travel
comparison = comparison.merge(
    selected_travel,
    left_on=partner_id_col,
    right_on=travel_partner_id_col,
    how="left",
    suffixes=("", "_travel")
)


# Calculate net earning from this order
payout = pd.to_numeric(
    selected_order["Payout"],
    errors="coerce"
)

travel_cost_col = find_column(
    comparison,
    [
        "One-Way Travel Cost (₹)",
        "Travel Cost (₹)",
        "Travel Cost"
    ]
)

if travel_cost_col is not None:
    comparison["Net Earning From Order (₹)"] = (
        payout
        - pd.to_numeric(
            comparison[travel_cost_col],
            errors="coerce"
        )
    )
else:
    comparison["Net Earning From Order (₹)"] = None


# Build clean comparison table
display_columns = []

possible_display_columns = [
    partner_name_col,
    "Location",
    "Distance (km)",
    "Mode of Transport",
    "Traffic Level",
    "ETA (min)",
    travel_cost_col,
    "Current Orders",
    "Busy Minutes Today",
    "Next Available Time",
    "Today Earnings",
    "Orders Completed Today",
    "Current Job Status",
    "Net Earning From Order (₹)"
]

for col in possible_display_columns:
    if col is not None and col in comparison.columns:
        display_columns.append(col)


comparison_display = comparison[
    display_columns
].copy()

st.dataframe(
    comparison_display,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# PARTNERFIT - SCORING ENGINE
# ==========================================

st.divider()
st.subheader("🧠 PartnerFit Decision Engine")

# Decision weights
WEIGHTS = {
    "ETA": 0.20,
    "Availability": 0.20,
    "Workload": 0.15,
    "Earnings Fairness": 0.15,
    "Experience": 0.10,
    "Reliability": 0.10,
    "Travel Cost": 0.05,
    "Distance": 0.05
}

st.write("### Decision Weights")

weights_df = pd.DataFrame({
    "Factor": WEIGHTS.keys(),
    "Weight": [f"{v*100:.0f}%" for v in WEIGHTS.values()]
})

st.dataframe(
    weights_df,
    use_container_width=True,
    hide_index=True
)

# ==========================================
# CALCULATE PARTNER SCORES
# ==========================================

st.write("### Partner Scores")

score_df = comparison.copy()

# ---------- ETA SCORE ----------
eta = pd.to_numeric(score_df["ETA (min)"], errors="coerce")
score_df["ETA Score"] = 100 * (
    eta.max() - eta
) / max(eta.max() - eta.min(), 1)

# ---------- DISTANCE SCORE ----------
distance = pd.to_numeric(
    score_df["Distance (km)"],
    errors="coerce"
)

score_df["Distance Score"] = 100 * (
    distance.max() - distance
) / max(distance.max() - distance.min(), 1)

# ---------- TRAVEL COST SCORE ----------
travel_cost = pd.to_numeric(
    score_df[travel_cost_col],
    errors="coerce"
)

score_df["Travel Cost Score"] = 100 * (
    travel_cost.max() - travel_cost
) / max(travel_cost.max() - travel_cost.min(), 1)

# ---------- WORKLOAD SCORE ----------
current_orders = pd.to_numeric(
    score_df["Current Orders"],
    errors="coerce"
)

busy_minutes = pd.to_numeric(
    score_df["Busy Minutes Today"],
    errors="coerce"
)

order_score = 100 * (
    current_orders.max() - current_orders
) / max(current_orders.max() - current_orders.min(), 1)

busy_score = 100 * (
    busy_minutes.max() - busy_minutes
) / max(busy_minutes.max() - busy_minutes.min(), 1)

score_df["Workload Score"] = (
    0.5 * order_score +
    0.5 * busy_score
)

# ---------- EARNINGS FAIRNESS ----------
today_earnings = pd.to_numeric(
    score_df["Today Earnings"],
    errors="coerce"
)

score_df["Earnings Fairness Score"] = 100 * (
    today_earnings.max() - today_earnings
) / max(
    today_earnings.max() - today_earnings.min(),
    1
)

# ---------- AVAILABILITY ----------
availability_col = find_column(
    score_df,
    ["Availability Commitment (Minutes)"]
)

if availability_col:
    availability = pd.to_numeric(
        score_df[availability_col],
        errors="coerce"
    )

    score_df["Availability Score"] = 100 * (
        availability - availability.min()
    ) / max(
        availability.max() - availability.min(),
        1
    )
else:
    score_df["Availability Score"] = 50


# ---------- SERVICE EXPERIENCE ----------
experience_map = {
    "Facial": "Facial Exp.",
    "Waxing": "Waxing Exp.",
    "Cleanup": "Cleanup Exp.",
    "Hair Spa": "Hair Spa Exp."
}

experience_col = experience_map.get(selected_service)

if experience_col in score_df.columns:
    experience = pd.to_numeric(
        score_df[experience_col],
        errors="coerce"
    )

    score_df["Experience Score"] = 100 * (
        experience - experience.min()
    ) / max(
        experience.max() - experience.min(),
        1
    )
else:
    score_df["Experience Score"] = 50


# ---------- RELIABILITY ----------
acceptance = pd.to_numeric(
    score_df["Acceptance Rate"]
    .astype(str)
    .str.replace("%", ""),
    errors="coerce"
)

completion = pd.to_numeric(
    score_df["Completion Rate"]
    .astype(str)
    .str.replace("%", ""),
    errors="coerce"
)

cancellation = pd.to_numeric(
    score_df["Cancellation Rate"]
    .astype(str)
    .str.replace("%", ""),
    errors="coerce"
)

rating = pd.to_numeric(
    score_df["Rating"],
    errors="coerce"
)

score_df["Reliability Score"] = (
    acceptance * 0.25
    + completion * 0.35
    + (100 - cancellation) * 0.20
    + (rating / 5 * 100) * 0.20
)


# ---------- FINAL PARTNERFIT SCORE ----------
score_df["PartnerFit Score"] = (
    score_df["ETA Score"] * WEIGHTS["ETA"]
    + score_df["Availability Score"] * WEIGHTS["Availability"]
    + score_df["Workload Score"] * WEIGHTS["Workload"]
    + score_df["Earnings Fairness Score"] * WEIGHTS["Earnings Fairness"]
    + score_df["Experience Score"] * WEIGHTS["Experience"]
    + score_df["Reliability Score"] * WEIGHTS["Reliability"]
    + score_df["Travel Cost Score"] * WEIGHTS["Travel Cost"]
    + score_df["Distance Score"] * WEIGHTS["Distance"]
)

score_df["PartnerFit Score"] = (
    score_df["PartnerFit Score"]
    .round(1)
)

score_df = score_df.sort_values(
    "PartnerFit Score",
    ascending=False
)

ranking_display = score_df[
    [
        partner_name_col,
        "Distance (km)",
        "ETA (min)",
        "Current Orders",
        "Busy Minutes Today",
        "Today Earnings",
        "Experience Score",
        "Reliability Score",
        "PartnerFit Score"
    ]
].copy()

st.dataframe(
    ranking_display,
    use_container_width=True,
    hide_index=True
)
