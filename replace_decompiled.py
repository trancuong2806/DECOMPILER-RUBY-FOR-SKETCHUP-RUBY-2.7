import os
import shutil
from pathlib import Path

def replace_decompiled_files():
    base_dir = Path(__file__).parent.absolute()
    target_dir = base_dir / "zsu" / "zsu_vn" # Đổi thành thư mục plugin mục tiêu
    
    if not target_dir.exists():
        print(f"Lỗi: Không tìm thấy thư mục đích '{target_dir}'")
        return

    print(f"Bắt đầu duyệt các file trong: {base_dir}")
    print(f"Thư mục đích: {target_dir}\n")

    # Lấy danh sách tất cả các file .rb trong zsu_vn và các thư mục con (duyệt đệ quy)
    target_files_map = {}
    for p in target_dir.rglob("*.rb"):
        if p.is_file():
            target_files_map[p.name] = p

    replaced_count = 0
    skipped_count = 0

    # Tìm tất cả file bắt đầu bằng 'decompiled_'
    for file_path in base_dir.glob("decompiled_*.rb"):
        if file_path.is_file():
            # Lấy tên file gốc bằng cách bỏ tiền tố 'decompiled_'
            original_filename = file_path.name.replace("decompiled_", "", 1)
            
            # Kiểm tra xem tên file gốc có tồn tại trong map không
            if original_filename in target_files_map:
                target_file_path = target_files_map[original_filename]
                try:
                    shutil.copy2(file_path, target_file_path)
                    print(f"[THÀNH CÔNG] Đã thay thế: {target_file_path.relative_to(base_dir)}")
                    replaced_count += 1
                except Exception as e:
                    print(f"[LỖI] Không thể copy {original_filename}: {e}")
            else:
                print(f"[BỎ QUA] Không tìm thấy file tương ứng cho: {original_filename}")
                skipped_count += 1

    print("\n--- TỔNG KẾT ---")
    print(f"Đã thay thế: {replaced_count} file")
    print(f"Đã bỏ qua: {skipped_count} file")

if __name__ == "__main__":
    replace_decompiled_files()
