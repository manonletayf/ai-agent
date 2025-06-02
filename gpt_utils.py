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
def find_companies(location, sector, goal=None, n_results=5, historic=[]):
    # Flatten historic_companies to a list of legal names
    excluding_names = []

    # Handle both dictionary and direct string cases
    for company in historic:
        if isinstance(company, dict) and "legal_name" in company:
            excluding_names.append(company["legal_name"])
        elif isinstance(company, str):
            excluding_names.append(company)
        
    exclusion_line = ""
    if excluding_names:
        exclusion_line = f"- Do not match any of the following companies: {', '.join(excluding_names)}"

    try:
        system_prompt = """
        You are an AI assistant helping identify the best potential clients for a workplace nursery scheme in London, specifically in London.

        You must only suggest companies that:
        - Have more than 1000 employees in London
        - Are among the top UK employers (e.g. Glassdoor or Sunday Times rankings)
        - Show interest in CSR (Corporate Social Responsibility), employee wellbeing, or HR-driven initiatives
        - Do NOT already provide their own childcare or nursery service
        
        Use approximate reasoning based on the company profile. Respond ONLY with a JSON array, where each element is an object with these fields:
        - legal_name: the official, registered name of the company (no extra text)
        - estimated_uk_size: the estimated number of employees in the UK (no extra text). If you don't know, use "unknown".
        Example:
        [
          {"legal_name": "Legal & General Group plc", "estimated_uk_size": 2000},
        ]
        """

        user_prompt = f"""
        Please identify {n_results} real companies based in {location if location else 'London'} {f',in the {sector} sector, ' if sector else ''} with more than 1000 employees.
        These companies should be potential candidates for:
        - {goal if goal is not None else 'a workplace childcare solution'}
        Make sure they:
        - Are top employers or have a strong HR brand
        - Care about CSR, employee wellbeing, or DEI
        - Do **not** already offer in-house childcare
        {exclusion_line}
        Return ONLY a JSON array, where each object has:
        - legal_name: the official, registered name of the company (no extra text)
        - estimated_uk_size: the estimated number of employees in the UK (no extra text). If you don't know, use "unknown".
        """
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

def get_domain_from_gpt(company_name):
    """
    Use GPT to guess the most likely domain name for a company.
    
    Args:
        company_name (str): The name of the company
        
    Returns:
        str: The predicted domain name, or None if there's an error
    """
    try:
        gpt_prompt = f"What is the most likely website domain of the company named {company_name}? only return the domain name without any other text."
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": gpt_prompt}],
            temperature=0.2,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ GPT failed to guess the domain: {e}")
        return None
