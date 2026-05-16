import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from io import BytesIO
import re
import unicodedata

# --- CONFIGURATION ---
# Link Google Sheets gốc (phần edit)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1YCPkfsalUisX-lLfcZRbyyu5Qx7JPoPDvUN4FRcnxxg/edit#gid=0"

st.set_page_config(
    page_title="AI Lead Scoring System", 
    layout="wide", 
    page_icon="🏙️"
)

# --- CUSTOM CSS (Độ giao diện) ---
st.markdown("""
    <style>
    /* Gradient background cho tiêu đề */
    .main {
        background-color: #f0f2f6;
    }
    .header-container {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF8F8F 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    /* Style cho Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #FF4B4B;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    /* Sidebar Logo placeholder */
    .sidebar-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- UTILS ---
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

# --- SCORING LOGIC ---
def calculate_score(description):
    if not isinstance(description, str) or pd.isna(description):
        return 0, "Không có dữ liệu"
    
    score = 0
    reasons = []
    
    desc_clean = description.lower()
    desc_no_accent = remove_accents(desc_clean)
    
    # 1. VIP Criteria (+50)
    vip_data = {
        "loai_hinh": ["biệt thự", "penthouse", "shophouse", "quỹ đất", "sàn văn phòng", "biet thu", "shop house"],
        "vi_tri": ["quận 1", "ven sông", "vinhomes", "phú mỹ hưng", "quan 1", "ven song"],
        "doi_tuong": ["chủ doanh nghiệp", "mua sỉ", "số lượng lớn", "tài chính mạnh", "chu doanh nghiep", "mua si"]
    }
    
    found_vip = False
    for category, kws in vip_data.items():
        for kw in kws:
            if kw in desc_clean or kw in desc_no_accent:
                score += 50
                reasons.append(f"⭐ VIP: {kw.title()}")
                found_vip = True
                break
        if found_vip: break

    # 2. Budget check (>= 20 tỷ)
    budget_match = re.search(r'(\d+[.,]?\d*)\s*tỷ', desc_clean)
    if budget_match:
        try:
            budget_str = budget_match.group(1).replace(',', '.')
            budget = float(budget_str)
            if budget >= 20:
                score += 50
                reasons.append(f"💰 Ngân sách lớn: {budget} tỷ")
            elif budget < 3 and ("quận 1" in desc_clean or "quan 1" in desc_no_accent):
                score -= 50
                reasons.append(f"⚠️ Giá phi thực tế tại Q1: {budget} tỷ")
        except:
            pass

    # 3. Trash Criteria (-50)
    trash_keywords = ["nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành", "hỏi giá cho vui", "bảo hiểm", "vay vốn", "mời chào", "thuê bao", "không phản hồi", "nham so", "khong co nhu cau"]
    for kw in trash_keywords:
        if kw in desc_clean or kw in desc_no_accent:
            score -= 50
            reasons.append(f"🚫 Dấu hiệu rác: {kw}")
            break

    if not reasons:
        reasons.append("⚡ Cần tư vấn thêm")
        
    return score, " | ".join(reasons)

def classify_lead(score):
    if score >= 50: return "🔥 Hot Lead"
    if score < 0: return "❄️ Cold/Trash"
    return "⚡ Warm Lead"

# --- SIDEBAR & FETCH ---
with st.sidebar:
    # Logo & Banner Section
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    # Sử dụng link logo MindX chính thức
    st.image("https://mindx.edu.vn/images/logo.png", width=150) 
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.header("⚙️ Cấu hình Hệ thống")
    st.info("Hệ thống đã kết nối bảo mật với Google Sheets.")
    
    if st.button("🔄 Tải & Chấm điểm AI", use_container_width=True, type="primary"):
        try:
            # Kiểm tra Secrets
            if "connections" not in st.secrets or "gsheets" not in st.secrets.connections:
                st.error("❌ Chưa tìm thấy cấu hình [connections.gsheets] trong Secrets!")
                st.stop()
                
            # Lấy cấu hình từ Secrets
            creds = dict(st.secrets.connections.gsheets)
            
            # TỰ ĐỘNG SỬA LỖI KEY (Dù bạn dán kiểu gì cũng sẽ chạy được)
            if "private_key" in creds:
                # 1. Chuyển \n văn bản thành xuống dòng thật
                fixed_key = creds["private_key"].replace("\\n", "\n")
                # 2. Loại bỏ các khoảng trắng thừa ở đầu/cuối mỗi dòng
                fixed_key = "\n".join([line.strip() for line in fixed_key.split("\n") if line.strip()])
                creds["private_key"] = fixed_key

            # Khởi tạo kết nối TRỰC TIẾP (Bỏ qua st.connection để tránh lỗi tham số)
            conn = GSheetsConnection(connection_name="gsheets", **creds)
            new_df = conn.read(spreadsheet=SHEET_URL, worksheet="0")
            
            if new_df is not None and not new_df.empty:
                # Xử lý chấm điểm
                results = new_df['nhu_cau_mo_ta'].apply(calculate_score)
                new_df['Score'] = [r[0] for r in results]
                new_df['Reason'] = [r[1] for r in results]
                new_df['Classification'] = new_df['Score'].apply(classify_lead)
                new_df['Status'] = new_df['Classification']
                
                st.session_state['lead_data'] = new_df
                st.success("✅ Tải dữ liệu thành success!")
                st.rerun()
            else:
                st.warning("⚠️ Không tìm thấy dữ liệu trong Sheet.")
        except Exception as e:
            st.error(f"❌ Lỗi kết nối: {str(e)}")
            st.markdown("---")
            st.warning("**Mẹo khắc phục:** Hãy kiểm tra lại phần Secrets. Đảm bảo `private_key` được dán đúng định dạng (không thừa khoảng trắng).")
    
    st.divider()
    st.write("---")
    st.caption("Developed by MindX Student")

# --- MAIN CONTENT ---
st.markdown("""
    <div class="header-container">
        <h1>🏙️ HỆ THỐNG AI LEAD SCORING</h1>
        <p>Phân loại khách hàng Bất động sản thông minh & Tự động</p>
    </div>
""", unsafe_allow_html=True)

if 'lead_data' in st.session_state and not st.session_state['lead_data'].empty:
    df = st.session_state['lead_data']
    
    # --- DASHBOARD METRICS (3 COLUMNS) ---
    st.subheader("📊 Chỉ số tổng quan")
    m1, m2, m3 = st.columns(3)
    
    total_leads = len(df)
    vip_leads = len(df[df['Score'] >= 50])
    trash_leads = len(df[df['Score'] < 0])
    
    m1.metric("🏠 Tổng khách hàng", f"{total_leads} Lead")
    m2.metric("🔥 Khách VIP (+50đ)", f"{vip_leads} Lead", delta=f"{vip_leads/total_leads:.1%}" if total_leads > 0 else "0%")
    m3.metric("❄️ Khách Rác (-50đ)", f"{trash_leads} Lead", delta=f"-{trash_leads/total_leads:.1%}" if total_leads > 0 else "0%", delta_color="inverse")
    
    st.divider()
    
    st.subheader("📋 Bảng Tổng kết Kiểm tra (Audit)")
    st.caption("Học viên kiểm duyệt kết quả AI trước khi xuất file Excel bàn giao.")
    
    # Data Editor
    edited_df = st.data_editor(
        df,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "ten_khach": st.column_config.TextColumn("👤 Khách hàng", disabled=True),
            "sdt": st.column_config.TextColumn("📞 SĐT", disabled=True),
            "nhu_cau_mo_ta": st.column_config.TextColumn("📝 Mô tả nhu cầu", width="large"),
            "Score": st.column_config.NumberColumn("🎯 Điểm", disabled=True, format="%d"),
            "Classification": st.column_config.TextColumn("🏷️ AI Phân loại", disabled=True),
            "Status": st.column_config.SelectboxColumn(
                "✅ Trạng thái chốt",
                options=["🔥 Hot Lead", "⚡ Warm Lead", "❄️ Cold/Trash", "🤝 Đã chốt", "❌ Hủy"],
                required=True
            ),
            "Reason": st.column_config.TextColumn("💡 Lý do AI", disabled=True)
        },
        hide_index=True,
        use_container_width=True,
        key="lead_editor_v2"
    )
    
    st.session_state['lead_data'] = edited_df

    # Actions
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='Leads_Final')
        
        st.download_button(
            label="📥 XUẤT FILE EXCEL BÀN GIAO CHO SALES",
            data=output.getvalue(),
            file_name="Leads_Report_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.warning("👋 Chào mừng! Hãy nhấn 'Tải & Chấm điểm AI' ở Sidebar để bắt đầu.")
    st.info("Hệ thống sẽ tự động quét Google Sheet và phân loại khách hàng dựa trên tiêu chí chấm điểm.")
    st.image("https://img.freepik.com/free-vector/data-processing-concept-illustration_114360-4611.jpg", width=600)
