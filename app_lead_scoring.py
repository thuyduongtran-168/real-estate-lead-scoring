import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import re
import unicodedata

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1YCPkfsalUisX-lLfcZRbyyu5Qx7JPoPDvUN4FRcnxxg/export?format=csv&gid=0"

st.set_page_config(page_title="AI Lead Scoring System", layout="wide", page_icon="🏙️")

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
    # Keywords (both accented and unaccented for robustness)
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
                reasons.append(f"VIP Category: {kw.title()}")
                found_vip = True
                break
        if found_vip: break

    # 2. Budget check (>= 20 tỷ) - Support decimals like 20.5 or 20,5
    budget_match = re.search(r'(\d+[.,]?\d*)\s*tỷ', desc_clean)
    if budget_match:
        try:
            budget_str = budget_match.group(1).replace(',', '.')
            budget = float(budget_str)
            if budget >= 20:
                score += 50
                reasons.append(f"Ngân sách lớn: {budget} tỷ")
            elif budget < 3 and ("quận 1" in desc_clean or "quan 1" in desc_no_accent):
                score -= 50
                reasons.append(f"Giá phi thực tế tại Q1: {budget} tỷ")
        except:
            pass

    # 3. Trash Criteria (-50)
    trash_keywords = ["nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành", "hỏi giá cho vui", "bảo hiểm", "vay vốn", "mời chào", "thuê bao", "không phản hồi", "nham so", "khong co nhu cau"]
    for kw in trash_keywords:
        if kw in desc_clean or kw in desc_no_accent:
            score -= 50
            reasons.append(f"Dấu hiệu rác: {kw}")
            break

    if not reasons:
        reasons.append("Tiềm năng trung bình/Cần tư vấn")
        
    return score, " | ".join(reasons)

def classify_lead(score):
    if score >= 50: return "🔥 Hot Lead"
    if score < 0: return "❄️ Cold/Trash"
    return "⚡ Warm Lead"

# --- UI SETUP ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 8px; height: 3em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🏙️ AI Lead Scoring & Automation")
st.caption("Giải pháp phân loại khách hàng thông minh cho ngành Bất động sản")

# --- SIDEBAR & FETCH ---
with st.sidebar:
    st.header("Cấu hình")
    if st.button("🔄 Tải & Chấm điểm mới", use_container_width=True, type="primary"):
        try:
            response = requests.get(SHEET_URL)
            new_df = pd.read_csv(BytesIO(response.content))
            
            # Apply AI Scoring
            results = new_df['nhu_cau_mo_ta'].apply(calculate_score)
            new_df['Score'] = [r[0] for r in results]
            new_df['Reason'] = [r[1] for r in results]
            new_df['Classification'] = new_df['Score'].apply(classify_lead)
            new_df['Status'] = new_df['Classification']
            
            st.session_state['lead_data'] = new_df
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi kết nối: {e}")
    
    st.divider()
    st.info("Hướng dẫn: Nhấn nút tải dữ liệu, sau đó kiểm duyệt trạng thái ở cột 'Trạng thái chốt' và xuất Excel.")

# --- MAIN CONTENT ---
if 'lead_data' in st.session_state and not st.session_state['lead_data'].empty:
    df = st.session_state['lead_data']
    
    # Dashboard Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng Lead", len(df))
    m2.metric("Hot Leads", len(df[df['Classification'] == "🔥 Hot Lead"]), delta_color="normal")
    m3.metric("Warm Leads", len(df[df['Classification'] == "⚡ Warm Lead"]))
    m4.metric("Cold/Trash", len(df[df['Classification'] == "❄️ Cold/Trash"]), delta_color="inverse")
    
    st.subheader("📋 Bảng kiểm duyệt (Human-in-the-loop)")
    
    # Data Editor
    edited_df = st.data_editor(
        df,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "ten_khach": st.column_config.TextColumn("Khách hàng", disabled=True),
            "sdt": st.column_config.TextColumn("SĐT", disabled=True),
            "nhu_cau_mo_ta": st.column_config.TextColumn("Mô tả nhu cầu", width="large"),
            "Score": st.column_config.NumberColumn("Điểm", disabled=True, format="%d"),
            "Classification": st.column_config.TextColumn("AI Phân loại", disabled=True),
            "Status": st.column_config.SelectboxColumn(
                "Trạng thái chốt",
                options=["🔥 Hot Lead", "⚡ Warm Lead", "❄️ Cold/Trash", "✅ Đã chốt", "❌ Hủy"],
                required=True
            ),
            "Reason": st.column_config.TextColumn("Lý do AI", disabled=True)
        },
        hide_index=True,
        use_container_width=True,
        key="lead_editor"
    )
    
    # Sync edited data back to session state
    st.session_state['lead_data'] = edited_df

    # Actions
    c1, c2 = st.columns([1, 1])
    with c2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='Leads')
        
        st.download_button(
            label="📥 Xuất Excel Bàn Giao",
            data=output.getvalue(),
            file_name="Leads_Report_Final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.warning("Chưa có dữ liệu. Vui lòng nhấn 'Tải & Chấm điểm mới' ở thanh bên trái.")
    st.image("https://img.freepik.com/free-vector/data-processing-concept-illustration_114360-4611.jpg", width=400)
