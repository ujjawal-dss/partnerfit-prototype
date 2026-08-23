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
