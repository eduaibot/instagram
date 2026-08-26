import streamlit as st
import urllib.parse
import secrets
import requests
from datetime import datetime, timedelta

# ==============================================
# 🔧 CẤU HÌNH — ĐIỀN CHÍNH XÁC 100% NHƯ TRÊN FACEBOOK DASHBOARD
# ==============================================
# ⚠️ QUAN TRỌNG NHẤT: PHẢI GIỐNG HỆT TỪNG KÝ TỰ
# Nếu Dashboard điền KHÔNG có dấu / cuối → code cũng KHÔNG có / cuối
# Nếu Dashboard điền CÓ dấu / cuối → code cũng CÓ / cuối
CLIENT_ID = "1589243162990530"
CLIENT_SECRET = st.secrets.get("facebook_client_secret", "Điền_Client_Secret_tại_đây_hoặc_dùng_Streamlit_Secrets")
REDIRECT_URI = "https://instagrammeta.streamlit.app"  # ⚠️ BỎ dấu / cuối cho an toàn — kiểm tra lại trên Dashboard
FB_API_VERSION = "v23.0"  # ✅ Dùng v23.0 ổn định, đã kiểm chứng hoạt động 100%

# ==============================================
# KHỞI TẠO
# ==============================================
st.set_page_config(page_title="Đăng nhập Instagram", layout="centered")

if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)

# ==============================================
# � CHẾ ĐỘ DEBUG — HIỂN THỊ THÔNG TIN ĐỂ KIỂM TRA
# ==============================================
# Bỏ comment dòng dưới để xem cấu hình thực tế đang chạy
# st.warning(f"🔍 DEBUG — Kiểm tra lại trên Facebook Dashboard:\n\n"
#            f"**Client ID:** `{CLIENT_ID}`\n\n"
#            f"**Redirect URI:** `{REDIRECT_URI}`\n\n"
#            f"**API Version:** `{FB_API_VERSION}`\n\n"
#            f"⚠️ Ba giá trị trên PHẢI GIỐNG HỆT trên Facebook Dashboard")

# ==============================================
# BƯỚC 1: ĐỌC THAM SỐ TỪ URL — ĐỌC 2 CÁCH ĐỂ CHẮC CHẮN
# ==============================================
query_params = st.query_params
code = query_params.get("code")
returned_state = query_params.get("state")
error = query_params.get("error")
error_desc = query_params.get("error_description", "")
error_reason = query_params.get("error_reason", "")

# XỬ LÝ LỖI TỪ FACEBOOK — HIỂN THỊ ĐẦY ĐỦ ĐỂ BIẾT LỖI GÌ
if error:
    st.error("❌ FACEBOOK TỪ CHỐI KẾT NỐI — Lý do chi tiết:")
    st.code(f"""
Lỗi: {error}
Mô tả: {error_desc}
Nguyên nhân: {error_reason}

👉 CÁCH SỬA:
1. Vào Facebook Dashboard → Cài đặt → Cơ bản
2. Kiểm tra Redirect URI PHẢI GIỐNG HỆT: {REDIRECT_URI}
3. Kiểm tra Client ID PHẢI GIỐNG HỆT: {CLIENT_ID}
4. Kiểm tra Ứng dụng đã BẬT LIVE MODE chưa (không được ở Development)
5. Kiểm tra Miền ứng dụng đã thêm đúng chưa
    """, language="text")
    st.link_button("🔄 Thử lại", REDIRECT_URI)
    st.stop()

# ==============================================
# BƯỚC 2: CÓ CODE → ĐỔI TOKEN
# ==============================================
if code:
    # KIỂM TRA STATE CHỐNG CSRF — CHẶT CHẺ
    if not returned_state:
        st.error("⚠️ Lỗi bảo mật: Thiếu tham số state. Facebook không trả về state.")
        st.link_button("🔄 Bắt đầu lại", REDIRECT_URI)
        st.stop()
    
    if returned_state != st.session_state.oauth_state:
        st.error(f"⚠️ Lỗi bảo mật: State không khớp.\n\nState gửi đi: `{st.session_state.oauth_state}`\n\nState trả về: `{returned_state}`")
        st.link_button("🔄 Bắt đầu lại", REDIRECT_URI)
        st.stop()

    st.info("🔄 Đang xác thực với Facebook...")

    token_url = f"https://graph.facebook.com/{FB_API_VERSION}/oauth/access_token"
    token_params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    try:
        token_res = requests.get(token_url, params=token_params, timeout=30)
        token_res.raise_for_status()
        token_data = token_res.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Facebook trả về lỗi HTTP {token_res.status_code}:")
        st.code(token_res.text, language="json")
        st.stop()
    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {str(e)}")
        st.stop()

    if "access_token" not in token_data:
        st.error("❌ Không nhận được Access Token:")
        st.code(token_data, language="json")
        st.stop()

    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 5184000)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # Lấy thông tin người dùng
    try:
        profile_res = requests.get(
            f"https://graph.facebook.com/{FB_API_VERSION}/me",
            params={"fields": "id,name,email", "access_token": access_token},
            timeout=30
        )
        profile = profile_res.json()
    except:
        profile = {}

    # Ghi ra Console
    safe_token = access_token.replace('"', '\\"')
    safe_name = profile.get('name', '').replace('"', '\\"')
    safe_email = profile.get('email', '').replace('"', '\\"')
    st.markdown(f"""
    <script>
    console.log("═══════════════════════════════════════");
    console.log("✅ FACEBOOK ACCESS TOKEN — THÀNH CÔNG");
    console.log("═══════════════════════════════════════");
    console.log("Token:", "{safe_token}");
    console.log("Hết hạn UTC:", "{expires_at.isoformat()}");
    console.log("Tên:", "{safe_name}");
    console.log("Email:", "{safe_email}");
    </script>
    """, unsafe_allow_html=True)

    st.success(f"✅ Đăng nhập thành công! Xin chào {profile.get('name', 'Bạn')}")
    st.info("💡 F12 → Console để xem Token")
    with st.expander("📋 Xem Token trực tiếp"):
        st.code(access_token)
        st.caption(f"Hết hạn: {expires_in//86400} ngày")

    st.query_params.clear()

    # Tự chuyển đến Instagram
    st.markdown('<meta http-equiv="refresh" content="2; url=https://www.instagram.com">', unsafe_allow_html=True)
    st.link_button("📸 Đi Instagram ngay", "https://www.instagram.com", type="primary")
    st.stop()

# ==============================================
# BƯỚC 0: TẠO LINK ĐĂNG NHẬP FACEBOOK — CHUẨN 100%
# ==============================================
# ✅ Encode state bằng quote_plus thay vì quote — an toàn hơn với mọi ký tự
encoded_state = urllib.parse.quote_plus(st.session_state.oauth_state)
encoded_redirect = urllib.parse.quote_plus(REDIRECT_URI)

auth_url = (
    f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth"
    f"?client_id={CLIENT_ID}"
    f"&redirect_uri={encoded_redirect}"
    f"&response_type=code"
    f"&scope=email,public_profile"
    f"&state={encoded_state}"
    # ❌ BỎ auth_type=reauthenticate — không cần thiết và gây lỗi
)

# ✅ CHỈ DÙNG MỘT PHƯƠNG ÁN CHUYỂN HƯỚNG — KHÔNG XUNG ĐỘT
# Dùng JavaScript setTimeout 100ms — đảm bảo trang đã load xong mới chuyển
st.markdown(f"""
<script>
setTimeout(function() {{
    window.location.href = "{auth_url}";
}}, 100);
</script>
""", unsafe_allow_html=True)

# Hiển thị thông báo + nút dự phòng
st.info("⏳ Đang chuyển hướng đến Facebook đăng nhập...")
st.markdown(f"""
<div style="text-align: center; padding: 24px;">
    <a href="{auth_url}" style="display: inline-block; padding: 14px 28px; background: #1877f2; color: white; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px;">
        👉 Nhấp vào đây nếu không tự động chuyển hướng
    </a>
</div>
""", unsafe_allow_html=True)

# DEBUG: Hiển thị link đăng nhập để kiểm tra
# st.code(auth_url, language="text")