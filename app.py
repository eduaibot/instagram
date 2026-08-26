import streamlit as st
import urllib.parse
import secrets

# ==============================================
# CẤU HÌNH — PHẢI TRÙNG KHỚP 100% VỚI FACEBOOK DASHBOARD
# ==============================================
CLIENT_ID = "1589243162990530"
CLIENT_SECRET = "Điền Client Secret từ Facebook Dashboard → Cài đặt → Ứng dụng"

# ⚠️ PHẢI GIỐNG HỆT trong: URI chuyển hướng hợp lệ + Miền ứng dụng
REDIRECT_URI = "https://instagrammeta.streamlit.app/"

FB_API_VERSION = "v24.0"

# ==============================================
# TẠO STATE CHỐNG CSRF
# ==============================================
if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)

st.set_page_config(page_title="Instagram Login", layout="centered")

# ==============================================
# BƯỚC 1: ĐỌC THAM SỐ TỪ URL
# ==============================================
query_params = st.query_params
code = query_params.get("code")
returned_state = query_params.get("state")
error = query_params.get("error")

if error:
    error_desc = query_params.get("error_description", "Không rõ lỗi")
    st.error(f"❌ Lỗi từ Facebook: {error_desc}")
    st.stop()

# ==============================================
# BƯỚC 2: CÓ CODE → ĐỔI TOKEN → LOG CONSOLE
# ==============================================
if code:
    if returned_state != st.session_state.oauth_state:
        st.error("⚠️ Lỗi bảo mật: State không khớp. Vui lòng thử lại.")
        st.stop()

    st.info("🔄 Đang xử lý...")

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
        st.error(f"❌ Không lấy được Token: {token_data}")
        st.stop()

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 5184000)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    profile_url = f"https://graph.facebook.com/{FB_API_VERSION}/me"
    profile_params = {"fields": "id,name,email", "access_token": access_token}
    profile_res = requests.get(profile_url, params=profile_params)
    profile = profile_res.json()

    # Ghi vào Console
    st.markdown(f"""
    <script>
    console.log("═══════════════════════════════════════");
    console.log("✅ FACEBOOK ACCESS TOKEN");
    console.log("═══════════════════════════════════════");
    console.log("Access Token:", "{access_token}");
    console.log("Hết hạn (giây):", {expires_in});
    console.log("Hết hạn UTC:", "{expires_at.isoformat()}");
    console.log("ID:", "{profile.get('id', '')}");
    console.log("Tên:", "{profile.get('name', '')}");
    console.log("Email:", "{profile.get('email', '')}");
    </script>
    """, unsafe_allow_html=True)

    st.success(f"✅ Đăng nhập thành công! Xin chào {profile.get('name', 'Bạn')}")
    st.info("💡 F12 → Tab Console để xem Token")
    st.query_params.clear()

    # Chuyển đến Instagram
    st.markdown("""
    <meta http-equiv="refresh" content="1; url=instagram://">
    <meta http-equiv="refresh" content="3; url=https://www.instagram.com">
    """, unsafe_allow_html=True)

    st.stop()

# ==============================================
# ✅ BƯỚC 0: TỰ ĐỘNG CHUYỂN HƯỚNG ĐẾN FACEBOOK — 100% HOẠT ĐỘNG
# ==============================================
auth_url = (
    f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?"
    f"client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=code"
    f"&scope=email,public_profile"
    f"&state={urllib.parse.quote(st.session_state.oauth_state)}"
)

st.info("⏳ Đang chuyển hướng đến Facebook đăng nhập...")

# ✅ FIX TRIỆT ĐỂ: Dùng META REFRESH — trình duyệt KHÔNG BAO GIỜ chặn
# Sau 0.5 giây tự động chuyển đến trang đăng nhập Facebook
st.markdown(f"""
<meta http-equiv="refresh" content="0.5; url={auth_url}">

<script>
// Phương án dự phòng nếu meta refresh không chạy
setTimeout(function() {{
    window.location.replace("{auth_url}");
}}, 800);
</script>
""", unsafe_allow_html=True)

# Nút dự phòng
st.markdown(f"[👉 Nhấp vào đây nếu không tự động chuyển hướng]({auth_url})")