import os
import streamlit as st
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from urllib.parse import urlencode
import hubspot
from hubspot.crm.companies import BatchReadInputSimplePublicObjectId

# Import all functions from utils.py
from utils import (
    check_authentication,
    enrich_contact_email,
    get_hubspot_company_lists,
    get_companies_from_hubspot_list,
    search_people,
    export_contacts_to_hubspot,
    main_app
)

load_dotenv()

# Initialize session state variables
if "results" not in st.session_state:
    st.session_state["results"] = []
if "selected_contacts" not in st.session_state:
    st.session_state["selected_contacts"] = []
if "hubspot_lists" not in st.session_state:
    st.session_state["hubspot_lists"] = pd.DataFrame()
if "hubspot_companies" not in st.session_state:
    st.session_state["hubspot_companies"] = []
if "all_companies" not in st.session_state:
    st.session_state["all_companies"] = []
if "domain_selection" not in st.session_state:
    st.session_state["domain_selection"] = []
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Authentication and main app execution
if __name__ == "__main__":
    # Check authentication first
    if check_authentication():
        main_app()
            