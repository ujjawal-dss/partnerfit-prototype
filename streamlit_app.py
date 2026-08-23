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

@st.cache_data(ttl=60)
def load_data():
    partners = pd.read_csv(PARTNERS_URL)
    services = pd.read_csv(SERVICES_URL)
    orders = pd.read_csv(ORDERS_URL)
    return partners, services, orders

st.title("PartnerFit")
st.caption("Yes Madam Partner Assignment Prototype")

try:
    partners, services, orders = load_data()

    st.success("Google Sheet connected successfully.")

    tab1, tab2, tab3 = st.tabs(["Partners", "Services", "Orders"])

    with tab1:
        st.subheader("Partners")
        st.dataframe(partners, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Services")
        st.dataframe(services, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Orders")
        st.dataframe(orders, use_container_width=True, hide_index=True)

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
