import streamlit as st
import pandas as pd
import requests
import time

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

# ==========================================
# LIVE LOCATION / ROUTING HELPERS
# ==========================================

@st.cache_data(ttl=86400)
def geocode_location(location_name):

    query = f"{location_name}, Noida, Uttar Pradesh, India"

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "PartnerFitInterviewPrototype/1.0"
    }

    for attempt in range(3):

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:

                data = response.json()

                if not data:
                    return None, None

                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])

                time.sleep(1.2)

                return lat, lon

            elif response.status_code in [429, 403]:

                time.sleep(3 + attempt * 2)

            else:
                time.sleep(2)

        except requests.RequestException:
            time.sleep(2 + attempt)

    return None, None

@st.cache_data(ttl=3600)
def get_osrm_route(
    origin_lat,
    origin_lon,
    destination_lat,
    destination_lon
):

    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{origin_lon},{origin_lat};"
        f"{destination_lon},{destination_lat}"
    )

    params = {
        "overview": "false"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if (
        data.get("code") != "Ok"
        or not data.get("routes")
    ):
        return None, None

    route = data["routes"][0]

    distance_km = route["distance"] / 1000
    eta_min = route["duration"] / 60

    return round(distance_km, 1), round(eta_min)

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

order_location_col = find_column(
    orders,
    ["Customer Location", "Location"]
)

partner_location_col = find_column(
    partners,
    ["Location", "Partner Location"]
)

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

# ==========================================
# LIVE ROUTING FOR ALL ELIGIBLE PARTNERS
# ==========================================

customer_location = selected_order[order_location_col]

customer_lat, customer_lon = geocode_location(
    customer_location
)

live_route_rows = []

if customer_lat is None or customer_lon is None:
    st.error(
        f"Could not locate customer location: {customer_location}"
    )
    st.stop()

with st.spinner("Calculating live routes for eligible partners..."):

    for _, partner in eligible_master.iterrows():

        partner_location = partner[partner_location_col]

        partner_lat, partner_lon = geocode_location(
            partner_location
        )

        if partner_lat is None or partner_lon is None:
            continue

        live_distance, live_eta = get_osrm_route(
            partner_lat,
            partner_lon,
            customer_lat,
            customer_lon
        )

        live_route_rows.append({
            "Partner ID": partner[partner_id_col],
            "Live Distance (km)": live_distance,
            "Live ETA (min)": live_eta
        })


live_routes_df = pd.DataFrame(live_route_rows)

st.write("### 🗺️ Live Routes — Eligible Partners")

st.dataframe(
    live_routes_df,
    use_container_width=True,
    hide_index=True
)





# Merge partner + workload
comparison = eligible_master.merge(
    workload,
    left_on=partner_id_col,
    right_on=workload_partner_id_col,
    how="left"
)

# Merge live routing data
comparison = comparison.merge(
    live_routes_df,
    left_on=partner_id_col,
    right_on="Partner ID",
    how="left",
    suffixes=("", "_live")
)

# Use LIVE distance and ETA for PartnerFit
comparison["Distance (km)"] = comparison["Live Distance (km)"]
comparison["ETA (min)"] = comparison["Live ETA (min)"]




# ==========================================
# LIVE TRAVEL COST CALCULATION
# ==========================================

payout = pd.to_numeric(
    selected_order["Payout"],
    errors="coerce"
)

# Get one transport mode per partner from Travel sheet
partner_mode_lookup = (
    travel[
        ["Partner ID", "Mode of Transport"]
    ]
    .drop_duplicates(subset=["Partner ID"])
)

comparison = comparison.merge(
    partner_mode_lookup,
    left_on=partner_id_col,
    right_on="Partner ID",
    how="left",
    suffixes=("", "_mode")
)

# Estimated cost per km by transport mode
cost_per_km = {
    "Scooter": 5,
    "Bike": 5,
    "Auto": 18,
    "Metro": 6,
    "Walking": 0
}

comparison["Cost Per KM (₹)"] = (
    comparison["Mode of Transport"]
    .map(cost_per_km)
    .fillna(5)
)

comparison["One-Way Travel Cost (₹)"] = (
    comparison["Distance (km)"]
    * comparison["Cost Per KM (₹)"]
).round(0)

travel_cost_col = "One-Way Travel Cost (₹)"

comparison["Net Earning From Order (₹)"] = (
    payout
    - comparison["One-Way Travel Cost (₹)"]
).round(0)

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
    score_df["Today Earnings"]
    .astype(str)
    .str.replace(",", "", regex=False),
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


# ==========================================
# FINAL RECOMMENDATION
# ==========================================

st.divider()
st.subheader("🏆 Recommended Partner")

# Top-ranked partner
best_partner = score_df.iloc[0]

best_name = best_partner[partner_name_col]
best_score = best_partner["PartnerFit Score"]

# Find nearest eligible partner
nearest_partner = score_df.sort_values(
    "Distance (km)",
    ascending=True
).iloc[0]

nearest_name = nearest_partner[partner_name_col]
nearest_distance = nearest_partner["Distance (km)"]

# Key metrics
best_distance = best_partner["Distance (km)"]
best_eta = best_partner["ETA (min)"]
best_orders = best_partner["Current Orders"]
best_busy = best_partner["Busy Minutes Today"]
best_today_earnings = best_partner["Today Earnings"]
best_reliability = best_partner["Reliability Score"]
best_experience = best_partner["Experience Score"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Recommended Partner",
        best_name
    )

with col2:
    st.metric(
        "PartnerFit Score",
        f"{best_score}/100"
    )

with col3:
    st.metric(
        "ETA",
        f"{best_eta} min"
    )

with col4:
    st.metric(
        "Distance",
        f"{best_distance} km"
    )

st.write("### Why this partner?")

reasons = []

# ETA reason
if best_partner["ETA Score"] >= 70:
    reasons.append(
        f"Fast ETA of {best_eta} minutes."
    )

# Workload reason
if best_partner["Workload Score"] >= 70:
    reasons.append(
        f"Low operational load: {best_orders} current order(s) "
        f"and {best_busy} busy minutes today."
    )

# Earnings fairness reason
if best_partner["Earnings Fairness Score"] >= 70:
    reasons.append(
        f"Lower earnings today (₹{best_today_earnings}), "
        f"supporting fairer order distribution."
    )

# Reliability
if best_partner["Reliability Score"] >= 90:
    reasons.append(
        f"Strong reliability score of "
        f"{best_reliability:.1f}/100."
    )

# Experience
if best_partner["Experience Score"] >= 70:
    reasons.append(
        f"Strong experience fit for {selected_service}."
    )

for reason in reasons:
    st.write("✅", reason)

# ==========================================
# DECISION EXPLAINABILITY
# ==========================================

st.write("### 🔎 How PartnerFit Made This Decision")

st.caption(
    "Eligible partners are ranked using operational efficiency, "
    "fairness, experience, reliability and travel factors."
)

factor_breakdown = pd.DataFrame([
    {
        "Factor": "ETA",
        "Factor Score": best_partner["ETA Score"],
        "Weight": "20%",
        "Weighted Contribution": best_partner["ETA Score"] * 0.20
    },
    {
        "Factor": "Availability",
        "Factor Score": best_partner["Availability Score"],
        "Weight": "20%",
        "Weighted Contribution": best_partner["Availability Score"] * 0.20
    },
    {
        "Factor": "Workload",
        "Factor Score": best_partner["Workload Score"],
        "Weight": "15%",
        "Weighted Contribution": best_partner["Workload Score"] * 0.15
    },
    {
        "Factor": "Earnings Fairness",
        "Factor Score": best_partner["Earnings Fairness Score"],
        "Weight": "15%",
        "Weighted Contribution": best_partner["Earnings Fairness Score"] * 0.15
    },
    {
        "Factor": "Experience",
        "Factor Score": best_partner["Experience Score"],
        "Weight": "10%",
        "Weighted Contribution": best_partner["Experience Score"] * 0.10
    },
    {
        "Factor": "Reliability",
        "Factor Score": best_partner["Reliability Score"],
        "Weight": "10%",
        "Weighted Contribution": best_partner["Reliability Score"] * 0.10
    },
    {
        "Factor": "Travel Cost",
        "Factor Score": best_partner["Travel Cost Score"],
        "Weight": "5%",
        "Weighted Contribution": best_partner["Travel Cost Score"] * 0.05
    },
    {
        "Factor": "Distance",
        "Factor Score": best_partner["Distance Score"],
        "Weight": "5%",
        "Weighted Contribution": best_partner["Distance Score"] * 0.05
    }
])

factor_breakdown["Factor Score"] = (
    factor_breakdown["Factor Score"].round(1)
)

factor_breakdown["Weighted Contribution"] = (
    factor_breakdown["Weighted Contribution"].round(1)
)

st.dataframe(
    factor_breakdown,
    use_container_width=True,
    hide_index=True
)

st.info(
    f"Final PartnerFit Score for {best_name}: "
    f"{best_score}/100"
)

# ------------------------------------------
# NEAREST VS RECOMMENDED COMPARISON
# ------------------------------------------

st.write("### Nearest Partner vs Recommended Partner")

if nearest_name != best_name:

    st.warning(
        f"The nearest eligible partner is {nearest_name} "
        f"at {nearest_distance} km, but PartnerFit recommends "
        f"{best_name}."
    )

    nearest_score = nearest_partner["PartnerFit Score"]

    compare_df = pd.DataFrame([
        {
            "Partner": nearest_name,
            "Distance (km)": nearest_partner["Distance (km)"],
            "ETA (min)": nearest_partner["ETA (min)"],
            "Current Orders": nearest_partner["Current Orders"],
            "Busy Minutes": nearest_partner["Busy Minutes Today"],
            "Today Earnings": nearest_partner["Today Earnings"],
            "Reliability": round(
                nearest_partner["Reliability Score"], 1
            ),
            "PartnerFit Score": nearest_score
        },
        {
            "Partner": best_name,
            "Distance (km)": best_partner["Distance (km)"],
            "ETA (min)": best_partner["ETA (min)"],
            "Current Orders": best_partner["Current Orders"],
            "Busy Minutes": best_partner["Busy Minutes Today"],
            "Today Earnings": best_partner["Today Earnings"],
            "Reliability": round(
                best_partner["Reliability Score"], 1
            ),
            "PartnerFit Score": best_score
        }
    ])

    st.dataframe(
        compare_df,
        use_container_width=True,
        hide_index=True
    )

    st.success(
        f"Decision: {best_name} is preferred because the "
        f"overall operational outcome is stronger, even though "
        f"{nearest_name} is closer."
    )

else:

    st.success(
        f"{best_name} is both the nearest eligible partner "
        f"and the highest-ranked partner."
    )

# ==========================================
# ASSIGN PARTNER ACTION
# ==========================================

st.divider()
st.subheader("✅ Assign Partner")

if st.button(
    f"Assign {best_name} to Order {selected_order_id}",
    type="primary"
):

    try:
        assignment_api_url = st.secrets["ASSIGNMENT_API_URL"]
        assignment_api_secret = st.secrets["ASSIGNMENT_API_SECRET"]

        response = requests.post(
            assignment_api_url,
            json={
                "secret": assignment_api_secret,
                "action": "assign",
                "order_id": selected_order_id,
                "partner_name": best_name
            },
            timeout=15
        )

        result = response.json()

        if result.get("success"):

            st.success(
                f"✅ Order {selected_order_id} assigned to {best_name}. "
                f"Google Sheet updated successfully."
            )

            st.cache_data.clear()

            assignment_summary = pd.DataFrame([
                {
                    "Order ID": selected_order_id,
                    "Service": selected_service,
                    "Assigned Partner": best_name,
                    "PartnerFit Score": best_score,
                    "ETA (min)": best_eta,
                    "Status": "Assigned"
                }
            ])

            st.write("### Assignment Summary")

            st.dataframe(
                assignment_summary,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.error(
                "Assignment failed: "
                + str(result.get("error"))
            )

    except Exception as e:
        st.error("Could not update Google Sheet.")
        st.code(str(e))

# ==========================================
# RESET DEMO DATA
# ==========================================

st.divider()
st.subheader("♻️ Reset Demo Data")

st.caption(
    "Use this after an interview to restore all orders "
    "for the next demo."
)

if st.button("♻️ Reset All Demo Orders"):

    try:
        assignment_api_url = st.secrets["ASSIGNMENT_API_URL"]
        assignment_api_secret = st.secrets["ASSIGNMENT_API_SECRET"]

        response = requests.post(
            assignment_api_url,
            json={
                "secret": assignment_api_secret,
                "action": "reset"
            },
            timeout=15
        )

        result = response.json()

        if result.get("success"):

            st.cache_data.clear()

            st.success(
                "✅ Demo reset complete! "
                "All orders are New and ready for the next interview."
            )

        else:
            st.error(
                "Reset failed: "
                + str(result.get("error"))
            )

    except Exception as e:
        st.error("Could not reset demo data.")
        st.code(str(e))
