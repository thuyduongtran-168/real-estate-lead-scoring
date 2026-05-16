# Skill: AI Lead Scoring & Automation (Ngành Bất Động Sản)

## 1. Mục tiêu (Objective)
Xây dựng quy trình chấm điểm khách hàng tiềm năng tự động dựa trên mô tả nhu cầu để tối ưu hóa việc phân loại và ưu tiên chăm sóc khách hàng trong ngành Bất động sản.

## 2. Cấu trúc dữ liệu đầu vào (Input Data)
Dữ liệu được lấy từ Google Sheets với các trường thông tin sau:
- `id`: Mã định danh khách hàng.
- `ten_khach`: Họ và tên khách hàng.
- `sdt`: Số điện thoại liên lạc.
- `nhu_cau_mo_ta`: Nội dung chi tiết về nhu cầu, ngân sách, vị trí và loại hình bất động sản khách hàng đang quan tâm.

## 3. Quy tắc chấm điểm (Scoring Rules)

### 3.1. Nhóm VIP / Siêu tiềm năng (Cộng 50 điểm)
AI cần nhận diện các từ khóa và ngữ cảnh sau trong trường `nhu_cau_mo_ta`:
- **Ngân sách lớn**: Đề cập số tiền từ **20 tỷ trở lên** hoặc cụm từ: "tài chính mạnh", "không thành vấn đề".
- **Loại hình cao cấp**: "Biệt thự đơn lập", "Penthouse", "Shophouse mặt đường lớn", "Quỹ đất công nghiệp", "Sàn văn phòng diện tích lớn".
- **Vị trí đắc địa**: "Quận 1", "Ven sông", "Vinhomes Ocean Park", "Phú Mỹ Hưng".
- **Đối tượng đặc biệt**: "Chủ doanh nghiệp", "Nhà đầu tư chuyên nghiệp", "Mua sỉ", "Mua số lượng lớn".
- **Tính cấp thiết & Pháp lý**: "Pháp lý chuẩn 100%", "Sổ hồng riêng", "Gặp trực tiếp chủ đầu tư để đàm phán".

### 3.2. Nhóm Rác / Không tiềm năng (Trừ 50 điểm)
AI cần loại bỏ hoặc đánh dấu thấp nếu phát hiện:
- **Yêu cầu phi thực tế**: Giá thấp vô lý (VD: Nhà Quận 1 giá 1-2 tỷ, nhà trung tâm có sân vườn giá vài trăm triệu).
- **Không có nhu cầu**: "Nhầm số", "Không có nhu cầu", "Dữ liệu cũ", "Nhầm ngành".
- **Không thiện chí**: "Hỏi giá cho vui", "Chưa có ý định mua", "Thái độ không hợp tác".
- **Spam/Quảng cáo**: Chứa nội dung "Bảo hiểm", "Vay vốn", "Mời chào dịch vụ".
- **Thông tin lỗi**: "Thuê bao", "Không phản hồi Zalo", "Gọi nhiều lần không bắt máy".

### 3.3. Nhóm Tiềm năng trung bình (Giữ nguyên hoặc cộng ít)
- Khách hàng mua chung cư, nhà phố tầm trung (**3-10 tỷ**).
- Khách hàng cần hỗ trợ vay ngân hàng, đang cân nhắc chính sách.
- Khách hàng có nhu cầu thực nhưng cần tư vấn thêm về pháp lý/vị trí.

## 4. Quy trình xử lý (Processing Flow)
1. **Trích xuất**: Đọc dữ liệu từ Google Sheets.
2. **Phân tích**: AI sử dụng NLP để phân tích ngữ nghĩa trong `nhu_cau_mo_ta`.
3. **Chấm điểm**: Áp dụng các quy tắc tại mục 3 để tính tổng điểm.
4. **Phân loại**:
   - **Hot Lead (> 50 điểm)**: Ưu tiên xử lý ngay.
   - **Warm Lead (0 - 50 điểm)**: Chăm sóc theo quy trình chuẩn.
   - **Cold/Trash Lead (< 0 điểm)**: Loại bỏ hoặc lưu trữ vào tệp khách hàng rác.

## 5. Đầu ra mong muốn (Output)
Dữ liệu sau khi xử lý phải được cập nhật lại vào hệ thống (hoặc xuất file Excel) bao gồm:
- Thông tin khách hàng ban đầu.
- Điểm số (Score).
- Phân loại (Hot/Warm/Cold).
- Ghi chú lý do chấm điểm của AI.
