@echo off
echo Building dumper.so for Ruby 2.7
gcc -shared -static-libgcc -Os -s -o dumper.so dumper.c minhook_dir/minhook-1.3.3/src/buffer.c minhook_dir/minhook-1.3.3/src/hook.c minhook_dir/minhook-1.3.3/src/trampoline.c minhook_dir/minhook-1.3.3/src/hde/hde64.c -I"minhook_dir/minhook-1.3.3/include" -I"D:/Ruby27-x64/include/ruby-2.7.0" -I"D:/Ruby27-x64/include/ruby-2.7.0/x64-mingw32" -L"D:/Ruby27-x64/lib" -lx64-msvcrt-ruby270
if %errorlevel% neq 0 (
    echo [FAIL] Build dumper failed!
) else (
    echo [OK] Build dumper success!
)
