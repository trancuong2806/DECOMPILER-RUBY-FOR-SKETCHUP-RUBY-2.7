# YARV Decompiler Architecture (Cấu trúc Decompiler YARV)

## 1. `decompiler/models.py` - Cấu trúc dữ liệu / Data Structure

**🇻🇳 Tiếng Việt:**
**Chức năng:** Định nghĩa các lớp dữ liệu nền tảng cho việc lưu trữ cấu trúc YARV.
- **Class `ISeq` (Instruction Sequence):** Đây là trung tâm của việc phân tích. Ruby biên dịch mã nguồn thành các chuỗi chỉ thị YARV (Instruction Sequence). Một object `ISeq` bao gồm:
  - `name`, `filepath`, `start_line`, `end_line`: Thông tin metadata định danh ngữ cảnh của đoạn bytecode.
  - `locals`: Bảng biến cục bộ của scope hiện tại.
  - `instructions`: Danh sách các lệnh (opcodes) và các tham số (arguments) tương ứng.
  - `catch_table`: Bảng xử lý ngoại lệ (lưu các block `rescue`, `ensure`).
  - `children`: Danh sách các `ISeq` con (đại diện cho các khối code `block`, phương thức `def`, hoặc `class` nằm bên trong).

*Logic: Thiết kế theo mô hình Cây (Tree Node), phù hợp để đệ quy phân tích cấu trúc lồng nhau của Ruby.*

**🇬🇧 English:**
**Function:** Defines foundational data classes for storing YARV structures.
- **Class `ISeq` (Instruction Sequence):** This is the center of analysis. Ruby compiles source code into YARV instruction sequences. An `ISeq` object includes:
  - `name`, `filepath`, `start_line`, `end_line`: Metadata identifying the context of the bytecode snippet.
  - `locals`: Local variable table of the current scope.
  - `instructions`: List of instructions (opcodes) and corresponding arguments.
  - `catch_table`: Exception handling table (stores `rescue`, `ensure` blocks).
  - `children`: List of child `ISeq`s (representing inner `block`s, `def` methods, or nested `class`es).
*Logic: Designed as a Tree Node model, suitable for recursively analyzing Ruby's nested structures.*

---

## 2. `decompiler/utils.py` - Tiện ích hỗ trợ / Utilities

**🇻🇳 Tiếng Việt:**
**Chức năng:** Các hàm xử lý chuỗi và dọn dẹp biến độc lập.
- **Xử lý định danh (`sanitize_ruby_identifier`):** Xóa bỏ các ký tự đặc biệt khỏi tên biến (ví dụ `block in map`) để biến nó thành một biến hợp lệ trong ngữ cảnh nội bộ của quá trình dịch ngược.
- **Xử lý cú pháp (`strip_outer_parens`, `wrap_if_complex`):** Ruby là ngôn ngữ có cú pháp linh hoạt (hỗ trợ bỏ ngoặc đơn). Logic này giúp loại bỏ ngoặc dư thừa như `((a + b))` thành `(a + b)`, đồng thời bọc ngoặc các biểu thức phức tạp khi làm tham số đầu vào.
- **Phân tích toán tử logic (`negate_expression`):** Phục vụ cho việc dịch ngược các vòng lặp `until` hoặc `unless`.
- **Kiểm tra luồng kết thúc (`is_unconditionally_terminating`):** Kiểm tra xem một đoạn code đã kết thúc bằng `return`, `raise` hay `exit` chưa, nhằm ngăn chặn việc chèn thêm các đoạn mã "Dead Code" dư thừa bên dưới.

**🇬🇧 English:**
**Function:** String manipulation and independent variable cleanup functions.
- **Identifier Processing (`sanitize_ruby_identifier`):** Removes special characters from variable names (e.g., `block in map`) to make them valid variables within the decompiler's internal context.
- **Syntax Processing (`strip_outer_parens`, `wrap_if_complex`):** Ruby has flexible syntax (optional parentheses). This logic removes redundant parentheses like `((a + b))` to `(a + b)`, while wrapping complex expressions when used as input parameters.
- **Logical Operator Analysis (`negate_expression`):** Serves the decompilation of `until` or `unless` loops.
- **Termination Flow Check (`is_unconditionally_terminating`):** Checks if a code block has unconditionally terminated with `return`, `raise`, or `exit` to prevent inserting redundant "Dead Code" below it.

---

## 3. `decompiler/parser.py` - Bộ phân tích cú pháp / Parser

**🇻🇳 Tiếng Việt:**
**Chức năng:** Đọc file log `.txt` do Dumper trả về và dịch nó thành cây `ISeq`.
- **`parse_dump(file_path)`:** Đọc từng dòng text và sử dụng RegEx để phân nhóm:
  - **Dòng `== disasm:`**: Đánh dấu sự khởi tạo của một `ISeq` mới, trích xuất tên, file và dải dòng của scope.
  - **Dòng `local table`**: Trích xuất các biến cục bộ (tên và cờ tag phân loại).
  - **Dòng `catch table`**: Nhận diện vùng bắt lỗi `rescue` và giới hạn byte của chúng (`st` và `ed`).
  - **Dòng lệnh bytecode**: Trích xuất mã offset (ví dụ `0000`), opcode (ví dụ `putobject`) và toàn bộ tham số phía sau.
- **Xây dựng cây cha-con:** Sử dụng hàm `get_nesting_level` (đếm số dấu cách thụt lề đầu dòng) để biết được `ISeq` nào là cha, `ISeq` nào là con, từ đó gán vào thuộc tính `children`.
*Nhận xét logic:* Trình Parser dựa trên indentation (thụt lề) là một cách làm rất thông minh và đặc thù vì đầu ra của lệnh `RubyVM::InstructionSequence.disasm` sử dụng khoảng trắng để thể hiện hệ thống phân cấp.

**🇬🇧 English:**
**Function:** Reads the `.txt` log file returned by the Dumper and translates it into an `ISeq` tree.
- **`parse_dump(file_path)`:** Reads each text line and uses RegEx to group:
  - **`== disasm:` line**: Marks the initialization of a new `ISeq`, extracting name, file, and line range of the scope.
  - **`local table` line**: Extracts local variables (names and classification tag flags).
  - **`catch table` line**: Identifies `rescue` error-catching areas and their byte limits (`st` and `ed`).
  - **Bytecode instruction lines**: Extracts offset codes (e.g., `0000`), opcodes (e.g., `putobject`), and all subsequent arguments.
- **Parent-Child Tree Construction:** Uses the `get_nesting_level` function (counting leading spaces/indentation) to determine which `ISeq` is the parent and which is the child, assigning them to the `children` attribute accordingly.
*Logic Observation:* The indentation-based Parser is a very smart and specific approach because the output of the `RubyVM::InstructionSequence.disasm` command uses spaces to represent hierarchy.

---

## 4. `decompiler/translator.py` - Bộ biên dịch ngược / Decompiler Core

**🇻🇳 Tiếng Việt:**
**Chức năng:** Abstract Interpreter (Trình thông dịch trừu tượng). Chuyển `ISeq` thành Ruby String thực sự.
Đây là bộ não lớn nhất và phức tạp nhất, hoạt động theo mô hình **Stack-based Simulation** (Giả lập ngăn xếp):
- **Stack Ảo (`stack`)**: Thay vì đưa dữ liệu thực vào Stack như khi chạy mã, translator đẩy "Cú pháp Ruby dưới dạng String" vào Stack. 
  - *Ví dụ:* Gặp `putobject 5`, đẩy `"5"` vào. Gặp `putobject 10`, đẩy `"10"` vào. Gặp `opt_plus`, pop `"10"`, pop `"5"`, đẩy `"(5 + 10)"` vào.
- **Hàm `translate_range(start_idx, end_idx)`**: Là một hàm đệ quy dịch từ vị trí dòng lệnh này đến dòng lệnh khác.
- **Xử lý rẽ nhánh (Branching & Control Flow):**
  - **If/Else (`branchif`, `branchunless`)**: Nó sử dụng thuật toán "Look-ahead" (nhìn về phía trước). Nó mô phỏng giả lập một stack của nhánh `then` và một stack của nhánh `else`. So sánh hai stack này: nếu kích thước thay đổi, đó là một khối rẽ nhánh. Còn nếu kích thước bằng nhau nhưng phần tử trên cùng khác nhau, đó là biểu thức trả về giá trị (ví dụ `cond ? a : b`).
  - **Vòng lặp (`while`, `until`)**: Phát hiện các lệnh `jump` có mục tiêu quay ngược lại lên trên (backward branch).
  - **Ngoại lệ (`rescue`)**: Khi quét qua các mã offset, so sánh với `catch_table`. Nếu trúng offset của block `rescue`, kích hoạt luồng biên dịch đoạn rẽ nhánh lỗi bằng cách gộp nhánh lệnh lại trong khối `begin...rescue...end`.
- **Dọn dẹp rò rỉ bộ nhớ Stack**: Phía cuối `translate_range`, thuật toán rà soát và xả các biến tạm rác (những định danh bị bỏ thừa trên stack không xài tới) dưới dạng các chuỗi riêng rẽ.
*Nhận xét logic:* Logic xử lý lệnh (Opcode Dispatch) thực chất là hàng trăm block `if op == '...'` rất đồ sộ. Việc giữ nó trong cùng một module là hợp lý vì các lệnh có tính liên kết chặt chẽ với nhau thông qua danh sách `stack` cục bộ.

**🇬🇧 English:**
**Function:** Abstract Interpreter. Converts `ISeq` into an actual Ruby String.
This is the largest and most complex brain, operating on a **Stack-based Simulation** model:
- **Virtual Stack (`stack`)**: Instead of pushing real data into the Stack like when running code, the translator pushes "Ruby Syntax as Strings" into the Stack. 
  - *Example:* Encounters `putobject 5`, pushes `"5"`. Encounters `putobject 10`, pushes `"10"`. Encounters `opt_plus`, pops `"10"`, pops `"5"`, pushes `"(5 + 10)"`.
- **Function `translate_range(start_idx, end_idx)`**: A recursive function translating from one instruction line position to another.
- **Branching & Control Flow:**
  - **If/Else (`branchif`, `branchunless`)**: It uses a "Look-ahead" algorithm. It simulates a stack for the `then` branch and a stack for the `else` branch. Compares these two stacks: if the size changes, it's a statement branch block. If the sizes are equal but the top elements differ, it's a value-returning expression (e.g., `cond ? a : b`).
  - **Loops (`while`, `until`)**: Detects `jump` instructions with upward targets (backward branches).
  - **Exceptions (`rescue`)**: When scanning through offset codes, it compares them with the `catch_table`. If it hits a `rescue` block's offset, it triggers the decompilation flow for the error branch by wrapping the instruction branches within a `begin...rescue...end` block.
- **Stack Memory Leak Cleanup**: At the end of `translate_range`, the algorithm reviews and flushes garbage temporary variables (unused identifiers abandoned on the stack) as separate strings.
*Logic Observation:* The instruction processing logic (Opcode Dispatch) is essentially hundreds of massive `if op == '...'` blocks. Keeping it in the same module is reasonable because the instructions are tightly coupled through the local `stack` list.

---

## 5. `decompiler/main.py` & `__main__.py` - Orchestrator (Điều phối)

**🇻🇳 Tiếng Việt:**
**Chức năng:** Giao tiếp với hệ điều hành và luồng đầu vào.
- **Khởi tạo:** Gọi `parse_dump` để nhận một mảng danh sách các đối tượng `ISeq`.
- **Lọc Entrypoint:** Tìm kiếm các `ISeq` gốc (có nhãn `<top (required)>` hoặc `<encoded>`) vì đó chính là scope ngoài cùng (Root level) của file mã nguồn.
- **Kích hoạt Dịch ngược:** Vòng lặp truyền `ISeq` gốc vào trong `translator.translate_iseq` để sinh ra chuỗi mã Ruby.
- **Ghi File:** Khởi tạo file mới với prefix `decompiled_...rb` và lưu lại nội dung. File `__main__.py` giúp chạy thư mục như một lệnh duy nhất: `python -m decompiler`.

**🇬🇧 English:**
**Function:** Interacts with the operating system and input flow.
- **Initialization:** Calls `parse_dump` to receive an array list of `ISeq` objects.
- **Entrypoint Filtering:** Searches for root `ISeq`s (labeled `<top (required)>` or `<encoded>`) because those are the outermost scopes (Root level) of the source code file.
- **Decompilation Trigger:** A loop passes the root `ISeq` into `translator.translate_iseq` to generate the Ruby code string.
- **File Writing:** Initializes a new file with the prefix `decompiled_...rb` and saves the content. The `__main__.py` file helps run the directory as a single command: `python -m decompiler`.
