# AI Agent - Contacts Finder

A Streamlit application for finding and enriching contacts from company domains using Apollo API and HubSpot integration.

## 🔐 Security Features

### Passcode Protection

The application now includes passcode protection to secure access. Users must enter a valid passcode before accessing the main application features.

#### Setting Up the Passcode

1. **Environment Variable (Recommended):**
   - Set the `APP_PASSCODE` environment variable in your `.env` file:
   ```
   APP_PASSCODE=your_secure_passcode_here
   ```

2. **Default Passcode:**
   - If no environment variable is set, the default passcode is: `contacts2024`

#### Using the Application

1. When you first access the app, you'll see a login screen
2. Enter the correct passcode to access the main application
3. Use the "🚪 Logout" button in the sidebar to end your session
4. The session will persist until you logout or close the browser

#### Features

- 🔒 Secure passcode-based authentication
- 🔄 Session persistence during use
- 🚪 Easy logout functionality
- 💡 User-friendly interface with helpful tips

## Features

- Import company domains from Excel files, manual input, or HubSpot lists
- Search for contacts using Apollo API with advanced filtering
- Enrich contacts with email addresses
- Export selected contacts to Excel
- Pagination and search result management
- HubSpot integration for company list management

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
APOLLO_API_KEY=your_apollo_api_key
HUBSPOT_ACCESS_TOKEN=your_hubspot_access_token
APP_PASSCODE=your_secure_passcode  # Optional, defaults to 'contacts2024'
```

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. **Authentication**: Enter the passcode to access the application
2. **Import Domains**: Upload Excel file, enter manually, or select from HubSpot lists
3. **Configure Search**: Set locations, job titles, and seniority filters
4. **Search**: Find contacts matching your criteria
5. **Select & Enrich**: Choose contacts and enrich with email addresses
6. **Export**: Download selected contacts as Excel file

## API Requirements

- **Apollo API**: For contact search and enrichment
- **HubSpot API**: For company list integration (optional)

## Security Notes

- Keep your passcode secure and change it regularly
- Use environment variables to store sensitive information
- Consider using a strong, unique passcode for production use
- The app uses session-based authentication - logout when finished
