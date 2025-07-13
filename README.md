# AI Agent - Contacts Finder

A Streamlit application for finding and enriching contacts from company domains using Apollo API and HubSpot integration.

## 🔐 Security Features

### Passcode Protection

The application includes passcode protection to secure access. Users must enter a valid passcode before accessing the main application features.

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
4. The session persists until you logout or close the browser

## ✨ Features

### 🔍 Domain Import Methods
- **Excel Upload**: Import company domains from Excel files (requires "Company Domain Name" column)
- **Manual Input**: Enter domains manually (one per line, without http:// or www.)
- **HubSpot Integration**: Select and import from existing HubSpot company lists

### 🎯 Advanced Search & Filtering
- **Location Filtering**: Optional location filters (up to 2 locations)
- **Job Title Targeting**: Specify job titles (up to 5 titles, separated by semicolons)
- **Seniority Levels**: Filter by seniority (owner, founder, c_suite, partner, vp, head, director, manager, senior, entry, intern)
- **Domain-Based Search**: Search contacts by company domain for more accurate results

### 📧 Contact Enrichment
- **Email Discovery**: Enrich selected contacts with verified email addresses using Apollo API
- **LinkedIn Integration**: Capture LinkedIn profile URLs when available
- **Real-time Enrichment**: Contacts are enriched on-demand when selected

### 📊 Results Management
- **Paginated Results**: Browse search results with pagination (10 results per page)
- **Selective Contact Management**: Choose specific contacts to enrich and export
- **Session Persistence**: Maintain selected contacts across page refreshes

### 📤 Export Options
- **Excel Export**: Download selected contacts as Excel files with all enriched data
- **HubSpot Export**: Create or add contacts to HubSpot lists with full property mapping
- **Comprehensive Data**: Export includes First Name, Last Name, Title, Company, Location, Email, LinkedIn, and Apollo ID

## 🛠️ Setup

### Prerequisites
- Python 3.7+
- Apollo API key
- HubSpot Access Token (optional, for HubSpot integration)

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables in `.env`:**
```env
APOLLO_API_KEY=your_apollo_api_key
HUBSPOT_ACCESS_TOKEN=your_hubspot_access_token  # Optional
APP_PASSCODE=your_secure_passcode  # Optional, defaults to 'contacts2024'
```

3. **Run the application:**
```bash
streamlit run app.py
```

## 📋 Usage Guide

### Step 1: Authentication
- Enter the passcode to access the application
- Use the logout button in the sidebar when finished

### Step 2: Import Company Domains
Choose one or more import methods:
- **Excel Upload**: Upload file with "Company Domain Name" column
- **Manual Entry**: Type domains one per line (e.g., google.com, microsoft.com)
- **HubSpot Lists**: Select from existing HubSpot company lists

### Step 3: Configure Search Filters
- **Select Domains**: Choose which imported domains to search
- **Location**: Optional location filters (e.g., "London ; Paris")
- **Job Titles**: Optional job title filters (e.g., "HR Director; Recruiter")
- **Seniority**: Optional seniority level filters

### Step 4: Search & Browse Results
- Click "Start Search" to find contacts
- Browse paginated results (10 per page)
- View contact details including name, title, company, location, and LinkedIn

### Step 5: Select & Enrich Contacts
- Click "Select and enrich" on desired contacts
- System automatically enriches contacts with email addresses
- Selected contacts are maintained in your session

### Step 6: Export Contacts
Choose your export method:
- **Excel Download**: Get immediate Excel file with all contact data
- **HubSpot Export**: Create or add to HubSpot lists with custom list names

## 🔧 API Requirements

### Apollo API
- **Purpose**: Contact search and email enrichment
- **Required**: Yes
- **Setup**: Add `APOLLO_API_KEY` to environment variables
- **Features Used**: People search, email enrichment

### HubSpot API
- **Purpose**: Company list integration and contact export
- **Required**: No (optional feature)
- **Setup**: Add `HUBSPOT_ACCESS_TOKEN` to environment variables
- **Features Used**: Company lists, contact creation, list management

## 📊 HubSpot Integration Details

### Company Lists
- Automatically loads available HubSpot company lists
- Supports multiple list retrieval methods for maximum compatibility
- Imports company domains from selected lists

### Contact Export
- **Property Mapping**:
  - Name → firstname, lastname
  - Title → jobtitle
  - Company → company
  - Location → city
  - Email → email
  - LinkedIn → hs_linkedin_url
- **Smart Handling**: Updates existing contacts, creates new ones as needed
- **List Management**: Automatically creates lists or adds to existing ones
- **Verification**: Optional membership verification after export

## 🔒 Security & Best Practices

### Authentication
- Use strong, unique passcodes for production
- Store sensitive information in environment variables
- Regularly rotate API keys and passcodes

### Data Privacy
- Contact data is processed in real-time and not permanently stored
- Session data is cleared on logout
- API keys are never exposed in the interface

### Performance
- Pagination prevents overwhelming the interface
- Rate limiting considerations for API calls
- Efficient session state management

## 🐛 Troubleshooting

### Common Issues

1. **"No HubSpot company lists found"**
   - Check HUBSPOT_ACCESS_TOKEN in environment
   - Verify token has proper scopes for list access

2. **"No contacts found" despite valid domains**
   - Verify Apollo API key is valid
   - Check if search filters are too restrictive
   - Ensure domains are entered without http:// or www.

3. **Contact enrichment failing**
   - Check Apollo API rate limits
   - Verify contact ID is valid
   - Ensure API key has enrichment permissions

### Debug Information
- The application provides detailed logging in the console
- Search parameters are displayed during operations
- Error messages include specific failure reasons

## 🤝 Contributing

This application is designed for internal use. For modifications:
1. Test changes thoroughly with sample data
2. Ensure API rate limits are respected
3. Maintain security best practices
4. Update documentation for any new features

## 📄 License

Internal use only. Contact administrator for usage permissions.
