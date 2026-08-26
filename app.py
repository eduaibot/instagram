import streamlit as st
import urllib.parse
import secrets
import requests
from datetime import datetime, timedelta

# ==============================================
# CẤU HÌNH — ĐỀN ĐẦY ĐỦ TRƯỚC KHI DÙNG
# ==============================================
CLIENT_ID = "1589243162990530"
CLIENT_SECRET = st.secrets.get("facebook_client_secret", "Điền Client Secret tại đây")
REDIRECT_URI = "https://instagrammeta.streamlit.app/"
FB_API_VERSION = "v24.0"

# ==============================================
# KHỞI TẠO
# ==============================================
st.set_page_config(page_title="Đăng nhập Instagram", layout="centered")

if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)

# ==============================================
# BƯỚC 1: NHẬN CODE TỪ FACEBOOK SAU KHI ĐĂNG NHẬP
# ==============================================
query_params = st.query_params
code = query_params.get("code")
returned_state = query_params.get("state")
error = query_params.get("error")

if error:
    st.error(f"❌ Lỗi: {query_params.get('error_description', 'Không rõ')}")
    st.link_button("🔄 Thử lại", REDIRECT_URI)
    st.stop()

# ==============================================
# BƯỚC 2: ĐỔI CODE → TOKEN → HIỂN THỊ
# ==============================================
if code:
    if not returned_state or returned_state != st.session_state.oauth_state:
        st.error("⚠️ Lỗi bảo mật, vui lòng thử lại.")
        st.link_button("🔄 Bắt đầu lại", REDIRECT_URI)
        st.stop()

    st.info("🔄 Đang xử lý...")

    token_url = f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token"
    token_params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    try:
        token_res = requests.get(token_url, params=token_params, timeout=30)
        token_data = token_res.json()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {str(e)}")
        st.stop()

    if "access_token" not in token_data:
        st.error(f"❌ Lỗi trả về: {token_data}")
        st.stop()

    access_token = token_data["access_token"]
    expires_at = datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 5184000))

    # Lấy thông tin người dùng
    profile_res = requests.get(
        f"https://graph.facebook.com/{FB_API_VERSION}/me",
        params={"fields": "id,name,email", "access_token": access_token},
        timeout=30
    )
    profile = profile_res.json()

    # In ra Console trình duyệt
    st.markdown(f"""
    <script>
    console.log("=== FACEBOOK ACCESS TOKEN ===");
    console.log(access_token = "{access_token}");
    console.log("Hết hạn:", "{expires_at.isoformat()} UTC");
    console.log("Tên:", "{profile.get('name','')}");
    console.log("Email:", "{profile.get('email','')}");
    </script>
    """, unsafe_allow_html=True)

    # Hiển thị kết quả
    st.success(f"✅ Xin chào {profile.get('name', 'Bạn')}!")
    st.info("💡 F12 → Console để xem Token")
    with st.expander("📋 Xem Token trực tiếp"):
        st.code(access_token)

    st.query_params.clear()

    # Tự chuyển đến Instagram sau 2 giây
    st.markdown('<meta http-equiv="refresh" content="2; url=https://www.instagram.com">', unsafe_allow_html=True)
    st.link_button("📸 Đi Instagram ngay", "https://www.instagram.com", type="primary")
    st.stop()

# ==============================================
# BƯỚC 0: AI MỞ LINK → TỰ NHẢY THẲNG ĐẾN FACEBOOK
# ==============================================
auth_url = (
    f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?"
    f"client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=code"
    f"&scope=email,public_profile"
    f"&state={urllib.parse.quote(st.session_state.oauth_state)}"
)

# === TỰ ĐỘNG CHUYỂN HƯỚNG NGAY LẬP TỨC ===
st.markdown(f"""
<meta http-equiv="refresh" content="0; url={auth_url}">
<script>window.location.replace("{auth_url}");</script>
""", unsafe_allow_html=True)

# Chỉ hiển thị khi trình duyệt chặn tự động chuyển
st.warning("⏳ Đang chuyển hướng đến Facebook...")
st.markdown(f"### 👉 [Nhấp vào đây nếu không tự động chuyển]({auth_url})")