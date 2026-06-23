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

## 4. `decompiler/translator.py` - Bộ biên dịch ngược (Orchestrator)

**🇻🇳 Tiếng Việt:**
**Chức năng:** Đóng vai trò là luồng điều hướng chính của việc giả lập Stack-based Simulation. Chuyển `ISeq` thành Ruby String thực sự.
- Trước đây file này là trái tim lớn nhất và phức tạp nhất, dài gần 1700 dòng. Tuy nhiên, logic xử lý các phép toán đơn giản đã được tách ra, file này hiện tại chỉ đóng vai trò Điều phối (Orchestrator) cho các vòng lặp, rẽ nhánh và gọi hàm phức tạp.
- **Xử lý rẽ nhánh (Branching & Control Flow):**
  - **If/Else (`branchif`, `branchunless`)**: Nó sử dụng thuật toán "Look-ahead" (nhìn về phía trước). Nó mô phỏng giả lập một stack của nhánh `then` và một stack của nhánh `else`. So sánh hai stack này: nếu kích thước thay đổi, đó là một khối rẽ nhánh. Còn nếu kích thước bằng nhau nhưng phần tử trên cùng khác nhau, đó là biểu thức trả về giá trị (ví dụ `cond ? a : b`).
  - **Vòng lặp (`while`, `until`)**: Phát hiện các lệnh `jump` có mục tiêu quay ngược lại lên trên (backward branch).
  - **Ngoại lệ (`rescue`)**: Khi quét qua các mã offset, so sánh với `catch_table`. Nếu trúng offset của block `rescue`, kích hoạt luồng biên dịch đoạn rẽ nhánh lỗi bằng cách gộp nhánh lệnh lại trong khối `begin...rescue...end`.

**🇬🇧 English:**
**Function:** Acts as the main navigation flow for the Stack-based Simulation. Converts `ISeq` into an actual Ruby String.
- Previously, this file was the largest and most complex heart, nearly 1700 lines long. However, the logic for processing simple operations has been extracted, and this file now acts as an Orchestrator for loops, branching, and complex function calls.
- **Branching & Control Flow:**
  - **If/Else (`branchif`, `branchunless`)**: It uses a "Look-ahead" algorithm. It simulates a stack for the `then` branch and a stack for the `else` branch. Compares these two stacks: if the size changes, it's a statement branch block. If the sizes are equal but the top elements differ, it's a value-returning expression (e.g., `cond ? a : b`).
  - **Loops (`while`, `until`)**: Detects `jump` instructions with upward targets (backward branches).
  - **Exceptions (`rescue`)**: When scanning through offset codes, it compares them with the `catch_table`. If it hits a `rescue` block's offset, it triggers the decompilation flow for the error branch by wrapping the instruction branches within a `begin...rescue...end` block.

---

## 5. Thư mục `decompiler/core/` - Kiến trúc tách rời / Decoupled Core

**🇻🇳 Tiếng Việt:**
**Chức năng:** Chứa logic nghiệp vụ được bóc tách từ `translator.py` nhằm giảm độ phức tạp và dễ bảo trì.
- **`core/handlers.py`**: Xử lý các Opcodes thuần tuý về mặt dữ liệu và thao tác ngăn xếp (Stack Manipulation).
  - Chứa hàm `handle_simple_op(op, args, stack, append_statement)`.
  - **Logic hoạt động bên trong:**
    1. **Rút trích tham số (Pop):** Với các phép toán hai ngôi (như `opt_plus`), hàm sẽ gọi `stack.pop()` hai lần để lấy ra vế phải (rhs) và vế trái (lhs).
    2. **Tối ưu cú pháp:** Sử dụng `strip_outer_parens` để bóc tách ngoặc đơn thừa trước khi ghép chuỗi, ngăn ngừa việc tạo ra các biểu thức bị lồng ngoặc quá sâu như `(((a + b) + c))`.
    3. **Đẩy kết quả (Push):** Ghép nối thành biểu thức Ruby hợp lệ (ví dụ `f"({lhs} + {rhs})"`) và đẩy ngược lại vào `stack`.
    4. **Tín hiệu điều khiển:** Hàm trả về `True` nếu đã xử lý thành công Opcode, giúp vòng lặp chính ở `translator.py` biết và bỏ qua (continue) việc kiểm tra các lệnh khác. Trả về `False` nếu đây là một Opcode phức tạp.
  - Hàm này bao thầu toàn bộ hàng chục Opcodes liên quan đến toán học (`opt_plus`, `opt_minus`, `opt_mult`), xử lý mảng/hash (`newarray`, `newhash`, `expandarray`), các phép so sánh (`opt_eq`, `opt_lt`, `opt_gt`), và các phép gán biến đổi trực tiếp trên Stack (`checktype`, `tostring`, `concatstrings`).
  - Việc tách rời module này giúp gỡ bỏ hơn 200 dòng code thừa thãi khỏi bộ máy chính, giúp dễ dàng kiểm thử các lệnh thao tác mảng/toán học mà không lo phá hỏng luồng Control Flow (if/else/loops).
- **`core/branching.py`** & **`core/__init__.py`**: Cấu trúc thiết kế mở giúp cô lập thêm các thuật toán "Look-ahead" (nhìn trước rẽ nhánh) của Decompiler sau này.

*Nhận xét logic:* Việc truyền tham chiếu list (`stack`) từ bộ máy chính `translator.py` vào `handlers.py` là một mô hình thiết kế tối ưu trong Python vì list là dạng truyền tham chiếu (pass by reference), giúp thay đổi được trạng thái ngăn xếp mà không cần phải nhúng toàn bộ kiến trúc Object Oriented Programming (OOP) rườm rà.

**🇬🇧 English:**
**Function:** Contains business logic extracted from `translator.py` to reduce complexity and improve maintainability.
- **`core/handlers.py`**: Handles pure data and stack-oriented Opcodes (Stack Manipulation).
  - Contains the function `handle_simple_op(op, args, stack, append_statement)`.
  - **Internal Logic Flow:**
    1. **Operand Extraction (Pop):** For binary operations (like `opt_plus`), it calls `stack.pop()` twice to extract the right-hand side (rhs) and left-hand side (lhs).
    2. **Syntax Optimization:** Uses `strip_outer_parens` to peel off redundant parentheses before formatting, preventing heavily nested expressions like `(((a + b) + c))`.
    3. **Result Insertion (Push):** Formats a valid Ruby expression (e.g., `f"({lhs} + {rhs})"`) and pushes it back onto the `stack`.
    4. **Control Signal:** Returns `True` if it successfully handled the Opcode, signaling the main loop in `translator.py` to skip further checks. Returns `False` if it's a complex Opcode requiring Orchestrator handling.
  - This function covers dozens of Opcodes related to mathematics (`opt_plus`, `opt_minus`, `opt_mult`), array/hash manipulation (`newarray`, `newhash`, `expandarray`), comparisons (`opt_eq`, `opt_lt`, `opt_gt`), and direct stack mutating assignments (`checktype`, `tostring`, `concatstrings`).
  - Decoupling this module removes over 200 lines of boilerplate from the main engine, making it easy to test array/math manipulation commands without breaking the highly complex Control Flow (if/else/loops).
- **`core/branching.py`** & **`core/__init__.py`**: An open design structure to further isolate "Look-ahead" branching algorithms of the Decompiler in the future.

*Logic Observation:* Passing the list reference (`stack`) from the main engine `translator.py` to `handlers.py` is an optimal design pattern in Python because lists are passed by reference, allowing the stack state to be modified without needing to embed a cumbersome full Object Oriented Programming (OOP) architecture.

---

## 6. `decompiler/main.py` & `__main__.py` - Orchestrator (Điều phối)

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
