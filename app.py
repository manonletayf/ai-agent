import streamlit as st
import pandas as pd
import re
from gpt_utils import (
    find_companies, find_new,
    generate_summary_for_targeting,
    suggest_additional_filters)
from hunter_utils import get_domain, get_contacts
import io

st.set_page_config(page_title="AI Company Finder", layout="centered")
st.title("AI Agent: Company Finder & Contact Enricher")

# --- Step 1: Define Company Criteria ---
st.header("Target Companies Finder")

location = st.text_input("📍 Location (optional)", placeholder="e.g. London, Manchester")
sector = st.text_input("🏭 Sector (optional)", placeholder="e.g. Legal, HR, Tech")
size = st.text_input("👥 Approximate Company Size (optional)", placeholder="e.g. 50+, mid-sized, under 500")
goal = st.text_input("🎯 Why are you targeting them?", placeholder="e.g. Offer a workplace childcare solution")
n_companies = st.slider("📦 Number of companies to generate", min_value=1, max_value=20, value=5)

# --- Load Companies ---
companies = st.session_state.get("companies", [])

if not companies:
    if st.button("Find Companies", use_container_width=True):
        with st.spinner("Thinking..."):
            companies = find_companies(location, sector, size, goal, n_results=n_companies)

        if not companies:
            st.warning("⚠️ GPT response couldn't be parsed or was empty.")
        else:
            st.session_state["companies"] = companies
            st.session_state['historic_companies'] = list(companies)

# Only show the list and export if companies exist
if companies:
    st.markdown("---")
    scores = {}
    for i, company in enumerate(companies):
        name = company["legal_name"]
        desc = company["description"]
        with st.expander(f"🔹 {name}"):
            st.write(desc)

    st.markdown('\n---')
    # Add Excel export for companies list
    output_companies = io.BytesIO()
    companies_df = pd.DataFrame(companies)
    with pd.ExcelWriter(output_companies, engine="xlsxwriter") as writer:
        companies_df.to_excel(writer, sheet_name="Companies", index=False)
        writer.close()
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=f"📤 Download Companies List (Excel)",
            data=output_companies.getvalue(),
            file_name="companies_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col2:
        if st.button("🔄 Reload results", use_container_width=True):
            st.session_state['companies'] = []
            with st.spinner("Thinking..."):
                new_companies = find_new(location, sector, size, goal, n_results=n_companies)
                st.session_state["companies"] = new_companies
            if st.session_state['companies'] == []:
                st.warning("⚠️ GPT response couldn't be parsed or was empty.")
            else:
                if 'historic_companies' not in st.session_state:
                    st.session_state['historic_companies'] = []
                st.session_state['historic_companies'].extend(new_companies)
                st.rerun()


    st.markdown('\n---')
    # --- Step 3: Find and Enrich Stakeholder Contacts ---
    st.header("Stakeholder Contacts Finder")

    selected_names = st.multiselect(
        "Select companies to analyze:",
        options=[c["legal_name"] for c in st.session_state.get('historic_companies', [])],
        default=[c["legal_name"] for c in st.session_state.get('companies', [])]
    )

    role_keywords = st.multiselect(
        "🎯 Filter contacts by decision-making roles:",
        ["HR", "Manager", "Director", "CEO", "Founder", "CTO", "COO", "CFO"],
        default=["HR", "Manager", "Director"]
    )
    role_keywords = [role.lower() for role in role_keywords]

    refresh_cache = st.checkbox("🔄 Refresh results (ignore cache)")
    if refresh_cache:
        st.cache_data.clear()
        st.info("✅ Cache cleared — data will be reloaded from Hunter.io")

    enriched_contacts = []

    if st.button("Find Stakeholder Contacts"):
        for company in companies:
            name = company["legal_name"]
            desc = company["description"]
            if name not in selected_names:
                continue

            st.subheader(f"🔍 {name}")
            with st.spinner("Searching domain..."):
                domain = get_domain(name)

                if domain == 'RATE_ERROR':
                    continue
                if not domain:
                    st.warning("🔄 Domain not found via Hunter.io, trying GPT...")
                    try:
                        from gpt_utils import client
                        gpt_prompt = f"What is the most likely website domain of the company named {name}? only return the domain name without any other text."
                        response = client.chat.completions.create(
                            model="gpt-4-1106-preview",
                            messages=[{"role": "user", "content": gpt_prompt}],
                            temperature=0.2,
                            max_tokens=20
                        )
                        domain = response.choices[0].message.content.strip()
                        st.info(f"✅ Domain suggested by GPT: `{domain}`")
                    except Exception as e:
                        st.error(f"❌ GPT failed to guess the domain: {e}")
                        continue

            if not domain:
                st.error("❌ No domain found for this company.")
                continue

            with st.spinner("Searching contacts via Hunter.io..."):
                contacts = get_contacts(domain, roles=role_keywords)
                if not contacts:
                    st.warning("No contacts found.")
                    continue

                for c in contacts[:5]:
                    st.markdown(
                        f"- **{c['name']}** — {c['position'] or 'N/A'}  "
                        f"📧 `{c['email']}`  🔗 {c['linkedin'] or 'No LinkedIn'}"
                    )
                    enriched_contacts.append({
                        "Company": name,
                        "Description": desc,
                        "Contact Name": c["name"],
                        "Position": c["position"] or "",
                        "Email": c["email"],
                        "LinkedIn": c["linkedin"] or "",
                        "Domain": domain
                    })

    # --- Export results to Excel ---
    if enriched_contacts:
        st.subheader("📄 Export Results (Excel)")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            contacts_df = pd.DataFrame(enriched_contacts)
            contacts_df.to_excel(writer, sheet_name="Stakeholder Contacts", index=False)
            writer.close()

        st.download_button(
            label="📤 Download Excel",
            data=output.getvalue(),
            file_name="stakeholder_contacts.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
# if companies:
#     st.markdown(f"### {len(companies)} companies generated.")
#     if 'enriched_contacts' in locals() and enriched_contacts:
#         st.markdown(f"### {len(enriched_contacts)} stakeholder contacts found.")
