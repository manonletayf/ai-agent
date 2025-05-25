from openai import OpenAI
import os
from dotenv import load_dotenv
import streamlit as st
import json
import re

# Load your .env variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.warning("⚠️ La clé API OpenAI est manquante. Vérifiez votre fichier .env.")

client = OpenAI(api_key=OPENAI_API_KEY)

# 1️⃣ FIND COMPANIES
@st.cache_data(show_spinner=False)
def find_companies(location, sector, size, goal, n_results=5):
    try:
        system_prompt = """
        You are an AI assistant helping identify the best potential clients for a workplace nursery scheme in the UK, specifically in London.

        You must only suggest companies that:
        - Have a large number of employees in London (e.g. 500+)
        - Are among the top UK employers (e.g. Glassdoor or Sunday Times rankings)
        - Show interest in CSR (Corporate Social Responsibility), employee wellbeing, or HR-driven initiatives
        - Do NOT already provide their own childcare or nursery service

        Use approximate reasoning based on the company profile. Respond ONLY with a JSON array, where each element is an object with these fields:
        - legal_name: the official, registered name of the company (no extra text)
        - description: one-sentence reason why they fit these criteria
        Example:
        [
          {"legal_name": "Legal & General Group plc", "description": "A top UK employer with a strong focus on employee wellbeing and CSR, based in London."},
          ...
        ]
        """

        user_prompt = (
            f"""
        Please identify {n_results} real companies based in {location or 'the UK'} {f'in the {sector} sector' if sector else ''} {f'with approximately {size} employees' if size else ''}.
        These companies should be potential candidates for:
        - {goal or 'a workplace childcare solution'}
        Make sure they:
        - Are top employers or have a strong HR brand
        - Care about CSR, employee wellbeing, or DEI
        - Do **not** already offer in-house childcare
        Return ONLY a JSON array, where each object has:
        - legal_name: the official, registered name of the company (no extra text)
        - description: one-sentence reason they match
        """
        )
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        # Remove Markdown code block if present (handles ```json ... ```)
        codeblock_match = re.match(r'^```(?:json)?\s*([\s\S]*?)\s*```$', content.strip(), flags=re.IGNORECASE)
        if codeblock_match:
            content = codeblock_match.group(1).strip()
        try:
            companies = json.loads(content)
        except Exception as e:
            st.error(f"❌ Failed to parse GPT JSON: {e}\nRaw output: {content}")
            return []
        return companies
    except Exception as e:
        st.error(f"❌ OpenAI — erreur lors de la recherche d'entreprises : {e}")
        return []

# 1️⃣ FIND COMPANIES
@st.cache_data(show_spinner=False)
def find_new(location, sector, size, goal, n_results=5):
    # Flatten historic_companies to a list of legal names
    historic = st.session_state.get("historic_companies", [])
    excluding_names = []
    for batch in historic:
        for company in batch:
            if isinstance(company, dict) and "legal_name" in company:
                excluding_names.append(company["legal_name"])

    exclusion_line = ""
    if excluding_names:
        exclusion_line = f"- Do not match any of the following companies: {', '.join(excluding_names[-20:])}"

    try:
        system_prompt = """
        You are an AI assistant helping identify the best potential clients for a workplace nursery scheme in the UK, specifically in London.

        You must only suggest companies that:
        - Have a large number of employees in London (e.g. 500+)
        - Are among the top UK employers (e.g. Glassdoor or Sunday Times rankings)
        - Show interest in CSR (Corporate Social Responsibility), employee wellbeing, or HR-driven initiatives
        - Do NOT already provide their own childcare or nursery service

        Use approximate reasoning based on the company profile. Respond ONLY with a JSON array, where each element is an object with these fields:
        - legal_name: the official, registered name of the company (no extra text)
        - description: one-sentence reason why they fit these criteria
        Example:
        [
          {"legal_name": "Legal & General Group plc", "description": "A top UK employer with a strong focus on employee wellbeing and CSR, based in London."},
          ...
        ]
        """

        user_prompt = (
            f"""
        Please identify {n_results} real companies based in {location or 'the UK'} {f'in the {sector} sector' if sector else ''} {f'with approximately {size} employees' if size else ''}.
        These companies should be potential candidates for:
        - {goal or 'a workplace childcare solution'}
        Make sure they:
        - Are top employers or have a strong HR brand
        - Care about CSR, employee wellbeing, or DEI
        - Do **not** already offer in-house childcare
        {exclusion_line}
        Return ONLY a JSON array, where each object has:
        - legal_name: the official, registered name of the company (no extra text)
        - description: one-sentence reason they match
        """
        )
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        content = response.choices[0].message.content
        # Remove Markdown code block if present (handles ```json ... ```)
        codeblock_match = re.match(r'^```(?:json)?\s*([\s\S]*?)\s*```$', content.strip(), flags=re.IGNORECASE)
        if codeblock_match:
            content = codeblock_match.group(1).strip()
        try:
            companies = json.loads(content)
        except Exception as e:
            st.error(f"❌ Failed to parse GPT JSON: {e}\nRaw output: {content}")
            return []
        return companies
    except Exception as e:
        st.error(f"❌ OpenAI — erreur lors de la recherche d'entreprises : {e}")
        return []
    
# 4️⃣ Résumé stratégique des critères
@st.cache_data(show_spinner=False)
def generate_summary_for_targeting(location, sector, size, goal):
    try:
        prompt = f"""
You are an assistant that summarizes B2B lead generation criteria in clear, strategic language. 
Summarize the following parameters into one paragraph suitable for a GPT prompt:

Location: {location or 'Any'}
Sector: {sector or 'Any'}
Company size: {size or 'Any'}
Goal: {goal or 'Offer a workplace nursery'}

Focus on HR, CSR and employee wellbeing priorities.
"""
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ Erreur GPT lors du résumé des critères : {e}")
        return ""

# 5️⃣ Suggestions avancées de filtres
@st.cache_data(show_spinner=False)
def suggest_additional_filters(location, sector, size, goal):
    try:
        prompt = f"""
You are a B2B marketing strategist helping design better GPT prompts for company prospecting.
Given the following target:

- Location: {location or 'Any'}
- Sector: {sector or 'Any'}
- Company Size: {size or 'Any'}
- Goal: {goal or 'Workplace childcare'}

What advanced filters, keywords, or attributes could help GPT identify companies that care about CSR, HR policies, and family wellbeing? List them in bullet points.
"""
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ Erreur GPT lors des suggestions de filtrage : {e}")
        return ""