import streamlit as st
import pandas as pd
import re
from gpt_utils import find_companies, score_company
from hunter_utils import get_domain, get_contacts
import io

st.set_page_config(page_title="AI Company Finder", layout="centered")
st.title("🤖 AI Agent: Company Finder & Contact Enricher")

# --- Step 1: Define Company Criteria ---
st.header("🔍 Step 1: Describe Your Target Companies")

location = st.text_input("📍 Location (optional)", placeholder="e.g. London, Manchester")
sector = st.text_input("🏭 Sector (optional)", placeholder="e.g. Legal, HR, Tech")
size = st.text_input("👥 Approximate Company Size (optional)", placeholder="e.g. 50+, mid-sized, under 500")
goal = st.text_input("🎯 Why are you targeting them?", placeholder="e.g. Offer a workplace childcare solution")
n_companies = st.slider("📦 Number of companies to generate", min_value=1, max_value=20, value=5)

if st.button("Find Companies"):
    with st.spinner("Thinking..."):
        raw_response = find_companies(location, sector, size, goal, n_results=n_companies)

    matches = re.findall(r"\d+\.\s+(.*?)(?:\s*\u2013\s*|\s*-\s*)(.*)", raw_response)
    companies = [(name.strip(), desc.strip()) for name, desc in matches]

    if not companies:
        st.warning("⚠️ GPT response couldn't be parsed. Here's the raw output:")
        st.markdown(raw_response)
    else:
        st.session_state["companies"] = companies

# --- Load Companies ---
companies = st.session_state.get("companies", [])

if companies:
    # --- Step 2: Score Companies ---
    st.header("📊 Step 2: Score Each Company")
    scores = {}
    for i, (name, desc) in enumerate(companies):
        with st.expander(f"🔹 {name}"):
            st.write(desc)
            if st.button(f"Score {name}", key=f"score-{i}"):
                with st.spinner("Scoring..."):
                    result = score_company(name, desc)
                st.success("✅ Scored!")
                st.write(result)
                scores[name] = result

    # --- Step 3: Find and Enrich Stakeholder Contacts ---
    st.header("👥 Step 3: Find Stakeholder Contacts")

    selected_names = st.multiselect(
        "Select companies to analyze:",
        options=[c[0] for c in companies],
        default=[c[0] for c in companies]
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
        for name, desc in companies:
            if name not in selected_names:
                continue

            st.subheader(f"🔍 {name}")
            with st.spinner("Searching domain..."):
                domain = get_domain(name)

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
                        "Score": scores.get(name, ""),
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
    
if companies:
    st.markdown(f"### ✅ {len(companies)} companies generated.")
    if enriched_contacts:
        st.markdown(f"### 👥 {len(enriched_contacts)} stakeholder contacts found.")
