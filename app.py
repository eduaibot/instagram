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
# BƯỚC 1: ĐỌC THAM SỐ TỪ URL (FACEBOOK TRẢ VỀ)
# ==============================================
query_params = st.query_params
code = query_params.get("code")
returned_state = query_params.get("state")
error = query_params.get("error")

# ==============================================
# XỬ LÝ LỖI TỪ FACEBOOK
# ==============================================
if error:
    error_desc = query_params.get("error_description", "Không rõ lỗi")
    st.error(f"❌ Lỗi từ Facebook: {error_desc}")
    st.stop()

# ==============================================
# BƯỚC 2: CÓ CODE → ĐỔI THÀNH ACCESS TOKEN → LOG VÀO CONSOLE
# ==============================================
if code:
    # Kiểm tra bảo mật state
    if returned_state != st.session_state.oauth_state:
        st.error("⚠️ Lỗi bảo mật: State không khớp. Vui lòng thử lại.")
        st.stop()

    st.info("🔄 Đang xử lý...")

    import requests
    from datetime import datetime, timedelta

    # Gọi Facebook API đổi Code → Access Token
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

    # Lấy thông tin user từ Facebook
    profile_url = f"https://graph.facebook.com/{FB_API_VERSION}/me"
    profile_params = {
        "fields": "id,name,email",
        "access_token": access_token
    }
    profile_res = requests.get(profile_url, params=profile_params)
    profile = profile_res.json()

    # ==============================================
    # ✅ GHI TOKEN + THÔNG TIN VÀO CONSOLE LOG
    # ==============================================
    console_script = f"""
    <script>
    console.log("═══════════════════════════════════════");
    console.log("✅ FACEBOOK ACCESS TOKEN ĐÃ NHẬN ĐƯỢC");
    console.log("═══════════════════════════════════════");
    console.log("Access Token:", "{access_token}");
    console.log("Hết hạn sau (giây):", {expires_in});
    console.log("Hết hạn vào (UTC):", "{expires_at.isoformat()}");
    console.log(" ");
    console.log("👤 THÔNG TIN NGƯỜI DÙNG:");
    console.log("Facebook ID:", "{profile.get('id', '')}");
    console.log("Tên:", "{profile.get('name', '')}");
    console.log("Email:", "{profile.get('email', '')}");
    console.log(" ");
    console.log("💡 Mở Tab Console (F12) để xem chi tiết");
    console.log("═══════════════════════════════════════");
    </script>
    """
    st.markdown(console_script, unsafe_allow_html=True)

    # Hiển thị cho người dùng thấy
    st.success(f"✅ Đăng nhập thành công! Xin chào {profile.get('name', 'Bạn')}")
    st.info("💡 Token đã được ghi vào Console. Nhấn F12 → Tab Console để xem.")

    # Xóa tham số khỏi URL cho sạch
    st.query_params.clear()

    # ==============================================
    # CHUYỂN HƯỚNG ĐẾN INSTAGRAM
    # ==============================================
    st.markdown("""
    <script>
    setTimeout(() => {
        window.top.location.href = "instagram://";
    }, 1000);
    setTimeout(() => {
        window.top.location.href = "https://www.instagram.com";
    }, 3000);
    </script>
    """, unsafe_allow_html=True)

    st.stop()

# ==============================================
# BƯỚC 0: CHƯA CÓ CODE → TỰ ĐỘNG CHUYỂN HƯỚNG ĐẾN FACEBOOK
# ==============================================
auth_url = (
    f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?"
    f"client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=code"
    f"&scope=email,public_profile"
    f"&state={urllib.parse.quote(st.session_state.oauth_state)}"
)

st.info("⏳ Đang chuyển hướng đến Facebook để đăng nhập...")

# ✅ FIX TRIỆT ĐỂ: TỰ ĐỘNG CHUYỂN HƯỚNG ĐÚNG CÁCH
# Dùng window.top.location.href để thoát khỏi IFRAME của Streamlit
st.markdown(f"""
<script>
(function() {{
    // Đợi trang tải xong rồi mới chuyển hướng
    if (document.readyState === "complete") {{
        redirectNow();
    }} else {{
        window.addEventListener("load", redirectNow);
    }}

    function redirectNow() {{
        console.log("🔄 Đang chuyển hướng đến Facebook...");
        // Dùng window.top để điều khiển trang CHÍNH, không phải IFRAME
        if (window.top && window.top !== window.self) {{
            window.top.location.href = "{auth_url}";
        }} else {{
            window.location.href = "{auth_url}";
        }}
    }}
}})();
</script>
""", unsafe_allow_html=True)

# Nút dự phòng nếu tự động không chạy
st.markdown(f"[👉 Nhấp vào đây nếu không tự động chuyển hướng]({auth_url})")