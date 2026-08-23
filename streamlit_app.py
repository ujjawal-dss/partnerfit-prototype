import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="PartnerFit",
    page_icon="🧑‍🔧",
    layout="wide"
)

SHEET_ID = "1yhe5-y05lVxroIqqBrXQG5_VfSA73G1ZZDCQEXwL5BY"

PARTNERS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Partners"
SERVICES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Services"
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

# Select Order
selected_order_id = st.selectbox(
    "Select Customer Order",
    orders["Order ID"].astype(str).tolist()
)

selected_order = orders[
    orders["Order ID"].astype(str) == selected_order_id
].iloc[0]

# Order details
selected_service = str(selected_order["Service"])

st.write("### Selected Order")
st.write("**Order ID:**", selected_order_id)
st.write("**Service:**", selected_service)

# Find service information
service_row = services[
    services["Service Name"].astype(str).str.lower()
    == selected_service.lower()
].iloc[0]

required_skill = str(service_row["Required Skill"])
required_kit = str(service_row["Required Kit"])

st.info(
    f"Required Skill: {required_skill} | Required Kit: {required_kit}"
)

# Check every partner
results = []

for _, partner in partners.iterrows():

    # ACTIVE CHECK
    active_value = str(partner["Active"]).strip().lower()
    active_ok = active_value in ["yes", "true", "1", "active"]

    # SKILL CHECK
    partner_skills = str(partner["Skills"]).strip().lower()
    skill_ok = required_skill.lower() in partner_skills

    # KIT CHECK
    partner_kit = str(partner["Kit Status"]).strip().lower()
    required_kit_clean = required_kit.lower().replace(" kit", "").strip()

    kit_ok = (
        required_kit_clean in partner_kit
        or partner_kit in ["available", "yes", "ready"]
    )

    # FINAL ELIGIBILITY
    eligible = active_ok and skill_ok and kit_ok

    results.append({
        "Partner": partner["Partner Name"],
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

# Show eligible partners only
eligible_partners = eligibility_df[
    eligibility_df["Eligible"] == "✅ YES"
]

if len(eligible_partners) > 0:

    st.success(
        f"{len(eligible_partners)} partner(s) eligible for this order."
    )

else:

    st.warning(
        "No partner currently satisfies the basic eligibility conditions."
    )
