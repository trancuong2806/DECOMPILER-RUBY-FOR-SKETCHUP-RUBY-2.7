# COMPILER RUBY FOR SKETCHUP 2020-2026
# Dự Án Dịch Ngược & Khôi Phục Mã Nguồn Plugin SketchUp Đang Sử Dụng rubyencoder (Không Áp Dụng Cho Các File .rbe)

Dự án này tập trung vào việc dịch ngược (decompile) bytecode Ruby YARV 2.7, khôi phục mã nguồn logic hoàn chỉnh của plugin SketchUp và thực hiện các quy trình kiểm thử tĩnh tự động để đảm bảo code sạch lỗi cú pháp (`Syntax OK`) và tuân thủ đúng SketchUp API.

---

## 1. Cấu Trúc Dự Án
### 🛠️ Bộ Công Cụ Dịch Ngược & Tối Ưu Core
* **[decompiler.py](file:///c:/Users/gauba/Downloads/project/decompiler.py)**: Bộ dịch ngược trung tâm, thực hiện giả lập stack của Ruby VM 2.7 YARV và chuyển đổi bytecode ngược lại thành mã nguồn Ruby tương ứng.
* **[auto_decompile.py](file:///c:/Users/gauba/Downloads/project/auto_decompile.py)**: Script tự động quét, dump bytecode và dịch ngược đồng loạt toàn bộ các file `.rb` mã hóa trong plugin.

---

## 2. Quy Trình Dịch Ngược & Đồng Bộ (Workflow)
* Yêu cầu cài đặt [Ruby+Devkit 2.7.0-1 (x64)](https://release-assets.githubusercontent.com/github-production-release-asset/78153411/386bbd80-2fc1-11ea-9af0-091632fb975f?sp=r&sv=2018-11-09&sr=b&spr=https&se=2026-06-16T07%3A00%3A02Z&rscd=attachment%3B+filename%3Drubyinstaller-devkit-2.7.0-1-x64.exe&rsct=application%2Foctet-stream&skoid=96c2d410-5711-43a1-aedd-ab1947aa7ab0&sktid=398a6654-997b-47e9-b12b-9515b896b4de&skt=2026-06-16T05%3A59%3A33Z&ske=2026-06-16T07%3A00%3A02Z&sks=b&skv=2018-11-09&sig=CVd9XAUm8YzPVXKpOre1KBSw4c3Hbg7V%2Fm50eFDy%2FQY%3D&jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmVsZWFzZS1hc3NldHMuZ2l0aHVidXNlcmNvbnRlbnQuY29tIiwia2V5Ijoia2V5MSIsImV4cCI6MTc4MTU5NDcwNywibmJmIjoxNzgxNTkxMTA3LCJwYXRoIjoicmVsZWFzZWFzc2V0cHJvZHVjdGlvbi5ibG9iLmNvcmUud2luZG93cy5uZXQifQ.yiIlqfPdfaN68Por4Dk427KEKa2Jq1NZWv8yTW_pAfI&response-content-disposition=attachment%3B%20filename%3Drubyinstaller-devkit-2.7.0-1-x64.exe&response-content-type=application%2Foctet-stream)
* Để thực hiện dịch ngược lại từ bytecode gốc sang mã nguồn Ruby hoàn chỉnh. Mở file **auto_decompiler.py** chỉnh sửa lại TARGET_DIR và RUBY_PATH:
```
RUBY_PATH = r"D:\Ruby27-x64\bin\ruby.exe" # Chọn đường dẫn cài đặt ruby
TARGET_DIR = r"" # Plugin Mục tiêu vd: MyPlugin\my_plugin
```

* Chạy chuỗi lệnh sau trong powershell tại thư mục gốc của dự án:

```powershell
Dịch ngược đồng loạt toàn bộ các file từ bytecode
python auto_decompile.py
```

---

## 3. Nguyên Lý Hoạt Động Của Decompiler (`decompiler.py`)

Bộ dịch ngược hoạt động dựa trên cơ chế phân tích tĩnh kết hợp với giả lập máy ảo Ruby YARV (Ruby 2.7):

### 3.1. Phân Tích Cấu Trúc ISeq (Instruction Sequence Parsing)
* Trích xuất thông tin metadata của phương thức/lớp từ tệp bytecode đã dump, bao gồm: bảng biến cục bộ (`local_table`), bảng xử lý biệt lệ (`catch_table`), số lượng tham số truyền vào, và danh sách chỉ thị bytecode chi tiết.

### 3.2. Giả Lập Ngăn Xếp (Stack Simulation)
* Vì Ruby YARV là máy ảo hoạt động dựa trên ngăn xếp (Stack-based VM), decompiler duy trì một `stack` giả lập (chứa các chuỗi biểu thức Ruby).
* Với mỗi chỉ thị bytecode, decompiler mô phỏng hành vi đẩy (push) hoặc rút (pop) tương ứng:
  * `putobject "hello"`: Đẩy `"hello"` lên stack.
  * `getlocal_WC_0 3`: Đọc tên biến tại vị trí thứ 3 trong bảng biến cục bộ và đẩy lên stack.
  * `opt_plus`: Pop hai biểu thức `a` và `b` từ stack và đẩy biểu thức gộp `"(a + b)"` ngược trở lại stack.

### 3.3. Tái Cấu Trúc Luồng Điều Khiển (Control Flow Reconstruction)
* Khi gặp các chỉ thị rẽ nhánh hoặc nhảy (`jump`, `branchunless`, `branchif`, `branchnil`), decompiler không dịch tuyến tính mà chuyển sang dịch đệ quy các nhánh bằng hàm `translate_range`:
  * Tạo các bản sao stack giả lập cho nhánh `then` và nhánh `else`.
  * Dịch thử nghiệm (lookahead) để xác định điểm hội tụ của các nhánh.
  * Ghép nối các nhánh thành cấu trúc điều khiển Ruby tương ứng: `if/else/end`, toán tử ba ngôi (`cond ? a : b`), toán tử logic ngắn mạch (`&&`, `||`), hoặc safe navigation (`&.`).

### 3.4. Dịch Đệ Quy Block & Phương Thức Con
* Đối với các chỉ thị định nghĩa block (`send` kèm block ISeq) hoặc định nghĩa phương thức (`definemethod`), decompiler thực hiện gọi đệ quy để khôi phục mã nguồn của block/phương thức đó, sau đó ghép nối chúng với ngữ cảnh cha bằng cú pháp block của Ruby (`do ... end` hoặc `{ ... }`).

---

## 4. Nguyên Lý Hoạt Động Của Bộ Trích Xuất Bytecode (`dumper.c`)

Để lấy được bytecode disassembly nguyên bản từ các tệp Ruby đã bị mã hóa hoặc nén (không thể đọc trực tiếp), dự án sử dụng bộ trích xuất viết bằng C (`dumper.c` biên dịch thành `dumper.so`):

### 4.1. Kỹ Thuật Đánh Chặn API (API Hooking)
* Sử dụng thư viện **MinHook** để can thiệp trực tiếp vào bảng export của DLL máy ảo Ruby 2.7 (`x64-msvcrt-ruby270.dll`).
* Đánh chặn hàm nội bộ **`rb_iseq_eval`** — hàm mà máy ảo Ruby bắt buộc phải gọi khi bắt đầu chạy một chuỗi chỉ thị ISeq (Instruction Sequence) mới nạp vào bộ nhớ.

### 4.2. Trích Xuất Bytecode Đệ Quy (Disassembly Extraction)
* Khi `rb_iseq_eval` bị kích hoạt, hàm hook `my_rb_iseq_eval` sẽ tạm thời giữ luồng điều khiển và truyền cấu trúc con trỏ `iseq` (kiểu `rb_iseq_t*`) sang hàm nội bộ **`rb_iseq_disasm`**.
* `rb_iseq_disasm` chuyển đổi toàn bộ cấu trúc dữ liệu ISeq nhị phân trong RAM thành chuỗi văn bản assembly mô tả chi tiết từng chỉ thị VM (YARV Assembly format).
* Dumper ghi chuỗi này trực tiếp vào file log **`dumped_code.txt`**.

### 4.3. Đảm Bảo Tính Trong Suốt (Transparent Execution)
* Sau khi trích xuất và ghi log, dumper gọi lại hàm gốc thông qua con trỏ `original_rb_iseq_eval(iseq)`.
* Điều này giúp quá trình trích xuất hoàn toàn trong suốt, không làm gián đoạn hay crash máy ảo Ruby, cho phép plugin ZSU chạy bình thường trong khi toàn bộ mã nguồn ẩn của nó bị lộ ra ở dạng assembly.

---


## 5. Các Cải Tiến Kỹ Thuật Nổi Bật Trên Decompiler

Trải qua các pha debug, bộ dịch ngược `decompiler.py` đã được nâng cấp đáng kể để khắc phục các lỗi nghiêm trọng của YARV bytecode:

### 5.1. Vá Lỗi Lệch Stack Do `branchnil` & Safe Navigation
* **Vấn đề cũ:** Khi lookahead dịch nhánh phụ của các biểu thức safe navigation inline nil-check dạng `(cond && cond.map...)`, bộ dọn dẹp stack leak ở cuối hàm vô tình pop sạch stack nền của context cha, gây lệch stack giả lập và mất mát cấu trúc Hash trả về ở cuối hàm.
* **Giải pháp:** 
  * Giới hạn block cleanup stack leak chỉ chạy tại root context (`if is_root:`).
  * Phát hiện sự khác biệt đỉnh stack giữa các nhánh phụ có độ dài bằng nhau để tự động gộp thành `(cond && expression)` hoặc `(cond || expression)` rồi thay thế đỉnh stack gốc.
  * Cấm các lệnh tạo mảng/hash (`newhash`, `newarray`...) trong helper xác định early return để tránh underflow stack và ngộ nhận return path.
* **Kết quả:** Khôi phục hoàn hảo Hash trả về chứa `:pts => pts_world` cuối hàm `compute_preview_for` trong `duckhung.rb`.

### 5.2. Hỗ Trợ Tối Ưu Hóa Mảng `opt_newarray_max` / `opt_newarray_min`
* **Vấn đề cũ:** Ruby VM tự động tối ưu hóa phép so sánh mảng tĩnh (ví dụ: `[a, b].max`) thành chỉ thị bytecode `opt_newarray_max`. Bộ dịch ngược cũ không hỗ trợ chỉ thị này khiến stack bị lỗi và sinh code rác.
* **Giải pháp:** Bổ sung trình xử lý cho `opt_newarray_max` và `opt_newarray_min` bằng cách pop số lượng phần tử tương ứng từ stack, đảo ngược thứ tự và đóng gói thành chuỗi Ruby `[elem1, elem2].max` hoặc `[elem1, elem2].min`.
* **Kết quả:** Phục hồi chính xác thuật toán tính khoảng cách hình học phức tạp `bbox_distance` in `banle.rb` không còn cảnh báo void context.

### 5.3. Dọn Dẹp Stack Lỗi Trong Phép Toán Gán Rẽ Nhánh (`pop` handler)
* **Vấn đề cũ:** Việc sử dụng `continue` trong trình xử lý lệnh `pop` khiến con trỏ lệnh `pc` không được tăng, tạo ra vòng lặp vô hạn và rút sạch stack giả lập làm mất phép gán `ds[:text_y] = ...` trong `preset.rb`.
* **Giải pháp:** Thay thế bằng cờ `is_filtered` để đảm bảo `pc += 1` luôn được gọi, kết hợp regex loại trừ các phép toán số học đơn giản và truy cập mảng/hash không gán khỏi cảnh báo void context.

### 5.4. Khôi Phục Toán Tử Gán Ngắn Mạch `||=` và `&&=`
* **Vấn đề cũ:** Khi dịch ngược các câu lệnh gán ngắn mạch (ví dụ: `v1x ||= line1_p1` trong `baoranh.rb`), do chỉ thị `setlocal` có cơ chế tự động đồng bộ stack và đổi tên phần tử trùng lặp còn lại ở đỉnh stack, decompiler cũ thiếu pattern matching đã tách nhánh này thành một phép gán vô điều kiện rác:
  ```ruby
  v1x = line1_p1
  (v1x || v1x)
  ```
* **Giải pháp:** Bổ sung logic gộp phép toán gán ngắn mạch trong chỉ thị `dup`. Nếu nhánh ngắn mạch chứa câu lệnh gán có dạng `{A_expr} = {RHS}`, decompiler sẽ pop câu lệnh đó ra khỏi danh sách câu lệnh tạm, trích xuất biểu thức bên phải và đóng gói lại thành biểu thức ngắn mạch chuẩn: `{A_expr} ||= {RHS}` (hoặc `&&=`).
* **Kết quả:** Phục hồi chính xác các biểu thức ngắn mạch trong `baoranh.rb` giúp tránh lỗi ghi đè giá trị vô điều kiện làm hỏng hình học CNC.

### 5.5. Tối Ưu Hóa Hiển Thị: Loại Bỏ Ngoặc Đơn Thừa & Định Dạng Keyword
* **Vấn đề:** Decompiler cũ sinh ra quá nhiều dấu ngoặc đơn lồng nhau khi cộng chuỗi dài (như trong `loader.rb`) hoặc khi gọi các hàm hệ thống, làm code trở nên khó đọc và không giống code viết tay.
* **Giải pháp:** 
  - Triển khai cơ chế **Smart Strip** cho các toán tử số học (`+`, `-`, `*`, `/`): Tự động bóc ngoặc vế trái nếu an toàn về mặt ưu tiên toán tử, biến `((a+b)+c)` thành `a+b+c`.
  - Chuyển đổi cách gọi `raise`, `exit`, `puts`, `require` sang dạng keyword (không ngoặc đơn) để đúng với style Ruby hiện đại.
  - Tích hợp bộ lọc bóc ngoặc tại tất cả các biên cú pháp: gán biến, điều kiện `if/while`, tham số hàm và phần tử Array/Hash.
* **Kết quả:** Mã nguồn `loader.rb` và các file nghiệp vụ giảm được hơn 40% lượng dấu ngoặc không cần thiết, đạt độ sạch tương đương mã nguồn gốc.

---

## 6. Trạng Thái Kiểm Thử Hiện Tại
* **Cú pháp:** **38/38 file** nghiệp vụ của plugin ZSU và **72/72 file** Ruby dịch ngược tổng thể (bao gồm các thư viện chuẩn) đều biên dịch thành công mà không có bất kỳ lỗi cú pháp (`Syntax OK`) nào.
* **SketchUp API:** Tuyệt đối tuân thủ hoa thường chuẩn của SketchUp (`Sketchup`, `Geom`, `UI`).
* **Unit Test:** `test_decompiler_opt_newarray.py` chạy thành công 100% (`TEST PASSED`).
