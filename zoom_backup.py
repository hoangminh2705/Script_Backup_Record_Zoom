import requests
import os
from datetime import datetime, timedelta

# --- CẤU HÌNH THÔNG TIN ---
ACCOUNT_ID = 'BlC4VojDRcWwqoG_0e6Uvw'
CLIENT_ID = 'dCtljs7nRk6v6JbWJTQSoA'
CLIENT_SECRET = '5ndyFRU4P7D3ErnnppYgnAUpqX5ttpzb'
DOWNLOAD_PATH = r'D:\backupzoom'

# Tên file log theo ngày chạy thực tế
current_date_str = datetime.now().strftime('%Y-%m-%d')
LOG_FILE = os.path.join(DOWNLOAD_PATH, f"backup_log_{current_date_str}.txt")

# Thiết lập mốc quét từ năm 2025 (hoặc 2024)
START_DATE = datetime(2025, 1, 1) 
END_DATE = datetime.now()

def write_log(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    print(message)
    os.makedirs(DOWNLOAD_PATH, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def get_access_token():
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ACCOUNT_ID}"
    try:
        response = requests.post(url, auth=(CLIENT_ID, CLIENT_SECRET))
        return response.json().get('access_token')
    except Exception as e:
        write_log(f"LỖI TOKEN: {e}")
        return None

def clean_filename(filename):
    for char in r'\/:*?"<>|':
        filename = filename.replace(char, "_")
    return filename.strip().replace(" ", "_")

def download_files():
    write_log(f"=== BẮT ĐẦU TIẾN TRÌNH BACKUP NGÀY {current_date_str} ===")
    token = get_access_token()
    if not token: 
        return

    headers = {'Authorization': f'Bearer {token}'}
    current_start = START_DATE

    while current_start < END_DATE:
        # Xác định khoảng thời gian 30 ngày chuẩn chỉnh
        current_end = current_start + timedelta(days=29)
        if current_end > END_DATE:
            current_end = END_DATE

        from_str = current_start.strftime('%Y-%m-%d')
        to_str = current_end.strftime('%Y-%m-%d')
        
        write_log(f"Đang quét dữ liệu từ: {from_str} đến {to_str}")
        
        # Gọi API với khoảng thời gian chính xác
        url = f"https://api.zoom.us/v2/users/me/recordings?from={from_str}&to={to_str}&page_size=300"
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            meetings = data.get('meetings', [])
        except Exception as e:
            write_log(f"Lỗi API tại khoảng {from_str}: {e}")
            meetings = []

        for meet in meetings:
            meeting_id = meet['id']
            # GIỮ NGUYÊN GIỜ UTC (Không cộng 7)
            raw_start_time = meet['start_time']
            start_time_obj = datetime.strptime(raw_start_time, '%Y-%m-%dT%H:%M:%SZ')
            time_str = start_time_obj.strftime('%Y-%m-%d_%Hh%M')
            
            topic = clean_filename(meet['topic'])
            # Đặt tên folder chứa cả Ngày_Giờ_Tên và ID cuộc họp để tránh trùng tên
            folder_name = f"{time_str}_{topic}_ID_{meeting_id}"
            meeting_dir = os.path.join(DOWNLOAD_PATH, folder_name)
            
            # Kiểm tra xem có file ghi âm/ghi hình nào không
            recording_files = meet.get('recording_files', [])
            if not recording_files:
                continue

            os.makedirs(meeting_dir, exist_ok=True)
            
            for file in recording_files:
                f_type = file['file_type']
                f_ext = file.get('file_extension', 'mp4').lower()
                d_url = f"{file['download_url']}?access_token={token}"
                f_name = f"{topic}_{f_type}.{f_ext}"
                f_path = os.path.join(meeting_dir, f_name)

                # Nếu file chưa tồn tại thì mới tải
                if not os.path.exists(f_path):
                    try:
                        write_log(f"-> Đang tải: {f_name}")
                        r = requests.get(d_url, timeout=120)
                        with open(f_path, 'wb') as f:
                            f.write(r.content)
                        write_log(f"   XONG: {f_name}")
                    except Exception as e:
                        write_log(f"   LỖI TẢI FILE: {f_name} - {e}")
                else:
                    # Đã có file thì bỏ qua không ghi log rác
                    pass

        # Tiến tới khoảng thời gian kế tiếp
        current_start = current_end + timedelta(days=1)

    write_log("=== KẾT THÚC TIẾN TRÌNH BACKUP ===")

if __name__ == "__main__":
    download_files()