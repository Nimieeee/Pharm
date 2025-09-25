# Authentication System Documentation

## Overview

This authentication system provides secure user authentication for the Pharmacology Chat App using Supabase Auth integration with Streamlit. The system includes user registration, login, session management, and route protection.

## Components

### 1. AuthenticationManager (`auth_manager.py`)
Handles core authentication operations with Supabase Auth:
- User registration (`sign_up`)
- User login (`sign_in`) 
- User logout (`sign_out`)
- Current user retrieval (`get_current_user`)
- Authentication status checking (`is_authenticated`)

### 2. SessionManager (`session_manager.py`)
Manages user sessions and Streamlit session state:
- Session initialization after login
- Session validation and refresh
- User preferences management (model, theme)
- Session cleanup on logout

### 3. AuthInterface (`auth_ui.py`)
Provides user interface components:
- Login form with validation
- Registration form with validation
- User profile sidebar
- Authentication page layout

### 4. AuthGuard (`auth_guard.py`)
Provides route protection and security:
- Authentication state checking
- Route protection decorators
- Session validation
- User context enforcement

## Setup Instructions

### 1. Streamlit Secrets Configuration
Configure your Supabase credentials using Streamlit secrets:

**Option A: Local Development**
Create `.streamlit/secrets.toml` in your project root:
```bash
mkdir -p .streamlit
cp secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your Supabase project details:
```toml
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
SUPABASE_SERVICE_KEY = "your_supabase_service_key"
```

**Option B: Streamlit Cloud**
Go to your app settings in Streamlit Cloud and add the secrets in the Secrets tab.

### 2. Database Setup
Ensure your Supabase project has the following table:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    subscription_tier TEXT DEFAULT 'free'
);
```

### 3. Running the Application
```bash
streamlit run auth_app.py
```

## Usage Examples

### Basic Authentication Check
```python
from auth_manager import AuthenticationManager
from session_manager import SessionManager
from auth_guard import AuthGuard

# Initialize components
auth_manager = AuthenticationManager()
session_manager = SessionManager(auth_manager)
auth_guard = AuthGuard(auth_manager, session_manager)

# Check if user is authenticated
if auth_guard.require_auth():
    # User is authenticated, show protected content
    st.write("Welcome to the protected area!")
else:
    # User is not authenticated, show login form
    st.write("Please log in to continue")
```

### Route Protection
```python
from auth_guard import RouteProtection

# Protect chat interface
if RouteProtection.protect_chat_interface(auth_guard):
    render_chat_interface()
```

### User Session Management
```python
# Get current user session
user_session = session_manager.get_user_session()
if user_session:
    st.write(f"Welcome, {user_session.email}!")
    
# Update user preferences
session_manager.update_model_preference("premium")
session_manager.update_theme("dark")
```

## Security Features

### 1. Session Validation
- Automatic session validation on each request
- Session refresh when needed
- Automatic cleanup of expired sessions

### 2. Route Protection
- Decorator-based route protection
- Automatic redirect to login for unauthorized access
- Session state validation

### 3. User Data Isolation
- User-scoped session management
- Secure user ID retrieval
- Protected user context enforcement

## Testing

Run the structure test to verify the authentication system:
```bash
python test_auth_mock.py
```

For full testing with Supabase credentials:
```bash
python test_auth.py
```

## Integration with Main App

The authentication system is designed to integrate seamlessly with the main Streamlit app:

```python
def main():
    # Initialize auth system
    auth_manager, session_manager, auth_guard, auth_ui = initialize_auth_system()
    
    # Check authentication
    if auth_guard.check_auth_state() == "authenticated":
        # Show main app
        render_main_app()
    else:
        # Show authentication page
        auth_ui.render_auth_page()
```

## Requirements Satisfied

This implementation satisfies the following requirements:

- **2.1**: Users are presented with authentication options
- **2.2**: Valid credentials grant access to the application
- **2.3**: Sign out terminates session and redirects to login
- **2.4**: Appropriate error messages for authentication failures
- **2.5**: Unauthenticated users cannot access chat functionality

## Next Steps

After authentication is set up:
1. Implement database schema and user data isolation (Task 2)
2. Create user-scoped message storage (Task 3)
3. Build RAG pipeline with user context (Task 4)
4. Integrate with chat interface (Task 7)