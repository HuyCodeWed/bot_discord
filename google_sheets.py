import gspread
from oauth2client.service_account import ServiceAccountCredentials
import discord

# --- PHẦN KẾT NỐI (Giữ nguyên) ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("acccounts").sheet1
except Exception as e:
    print(f"Lỗi khi kết nối tới Google Sheets: {e}")
    # Có thể thêm xử lý thoát chương trình ở đây nếu kết nối thất bại
    # exit()

# --- HÀM LẤY TÀI KHOẢN (ĐÃ CẬP NHẬT) ---
def get_all_accounts():
    """Đọc tất cả tài khoản từ sheet và trả về danh sách."""
    try:
        # Lấy tất cả các dòng, bỏ qua dòng tiêu đề đầu tiên
        rows = sheet.get_all_values()[1:]
        accounts = []
        
        for row in rows:
            # THAY ĐỔI Ở ĐÂY: Kiểm tra xem dòng có đủ 6 cột không
            if len(row) >= 6:
                # Đảm bảo chỉ lấy 6 cột để tránh lỗi nếu có cột thừa
                account_data = row[:6]
                accounts.append(account_data)

        return accounts
    except gspread.exceptions.SpreadsheetNotFound:
        print("Lỗi: Không tìm thấy spreadsheet có tên 'acccounts'.")
        return []
    except Exception as e:
        print(f"Lỗi khi đọc dữ liệu từ sheet: {e}")
        return []

# --- HÀM XÓA TÀI KHOẢN (KHÔNG CẦN THAY ĐỔI) ---
def delete_account_by_stt(stt):
    """Tìm tài khoản theo STT, xóa dòng đó và trả về dữ liệu của dòng đã xóa."""
    try:
        # Tìm ô chứa STT
        cell = sheet.find(str(stt), in_column=1)
        if cell:
            # Lấy toàn bộ dữ liệu của dòng đó trước khi xóa
            row_data = sheet.row_values(cell.row)
            # Xóa dòng
            sheet.delete_rows(cell.row)
            # Trả về dữ liệu (giờ đã có 6 cột)
            return row_data
        return None
    except Exception as e:
        print(f"Lỗi khi xóa tài khoản STT {stt}: {e}")
        return None