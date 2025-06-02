# AI-powered Company Finder and Contact Enrichment Tool

This project is an AI-powered tool designed to identify target companies based on specific criteria and enrich them with stakeholder contact information. It leverages the OpenAI API for company identification and the Hunter.io API for contact discovery. The Streamlit-based application provides a user-friendly interface for defining company criteria, finding companies, and exporting the results.

## Key Features

*   **Company Finder:** Uses GPT to identify companies based on location, sector, and specific goals.
*   **Contact Enrichment:** Leverages Hunter.io to find stakeholder contact information within identified companies.
*   **Streamlit Interface:** Provides an interactive user interface for easy use.
*   **Data Export:** Allows exporting company and contact data to Excel files.

## Usage

1.  **Set up your environment:**
    *   Install the required packages: `pip install -r requirements.txt`
    *   Set your OpenAI and Hunter.io API keys as environment variables.
2.  **Run the application:** `streamlit run app.py`
