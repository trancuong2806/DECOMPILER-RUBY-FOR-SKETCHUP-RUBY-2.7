#include <ruby.h>
#include <windows.h>
#include "minhook_dir/minhook-1.3.3/include/MinHook.h"
#include <stdio.h>

/*
 * Project: DECOMPILER RUBY FOR SKETCHUP RUBY 2.7
 * Author: Trần Cường
 * Created: 16/06/2026
 * License: BSD 2-Clause License
 * Description: This module handles decompiling Ruby scripts for SketchUp.
 * Copyright (c) 2026, Tran Cuong. All rights reserved.
 */

typedef void* (*rb_iseq_eval_t)(void *iseq);
rb_iseq_eval_t original_rb_iseq_eval = NULL;

typedef VALUE (*rb_iseq_disasm_t)(void *iseq);
rb_iseq_disasm_t p_rb_iseq_disasm = NULL;

FILE *log_file = NULL;

// Hàm giả mạo cho rb_iseq_eval
void* my_rb_iseq_eval(void *iseq) {
    if (log_file) {
        fprintf(log_file, "========================================================\n");
        fprintf(log_file, "[DUMPER] Bắt đầu gọi rb_iseq_eval cho iseq: %p\n", iseq);
        
        if (p_rb_iseq_disasm) {
            // iseq ở đây là rb_iseq_t*
            VALUE disasm_str = p_rb_iseq_disasm(iseq);
            if (!NIL_P(disasm_str) && TYPE(disasm_str) == T_STRING) {
                char *str = StringValueCStr(disasm_str);
                fprintf(log_file, "%s\n", str);
            } else {
                fprintf(log_file, "[DUMPER] Lỗi: rb_iseq_disasm trả về kết quả không hợp lệ!\n");
            }
        } else {
            fprintf(log_file, "[DUMPER] Không thể gọi rb_iseq_disasm do không tìm thấy hàm.\n");
        }
        
        fprintf(log_file, "========================================================\n\n");
        fflush(log_file);
    }
    
    // Gọi lại hàm gốc để máy ảo Ruby vẫn hoạt động bình thường
    return original_rb_iseq_eval(iseq);
}

// Khởi tạo thư viện Dumper
void Init_dumper() {
    log_file = fopen("dumped_code.txt", "w");
    if (log_file) {
        fprintf(log_file, "[DUMPER] Đã tải thư viện dumper!\n");
        fflush(log_file);
    }

    if (MH_Initialize() != MH_OK) {
        if (log_file) fprintf(log_file, "[DUMPER] MH_Initialize thất bại.\n");
        return;
    }

    // Lấy module handle của Ruby 2.7
    HMODULE hRuby = GetModuleHandle("x64-msvcrt-ruby270.dll");
    if (!hRuby) {
        if (log_file) fprintf(log_file, "[DUMPER] Không tìm thấy x64-msvcrt-ruby270.dll\n");
        return;
    }

    void *p_rb_iseq_eval = (void *)GetProcAddress(hRuby, "rb_iseq_eval");
    p_rb_iseq_disasm = (rb_iseq_disasm_t)GetProcAddress(hRuby, "rb_iseq_disasm");

    if (p_rb_iseq_eval) {
        if (MH_CreateHook(p_rb_iseq_eval, &my_rb_iseq_eval, (LPVOID*)&original_rb_iseq_eval) == MH_OK) {
            MH_EnableHook(p_rb_iseq_eval);
            if (log_file) fprintf(log_file, "[DUMPER] Đã hook rb_iseq_eval thành công tại %p\n", p_rb_iseq_eval);
        } else {
            if (log_file) fprintf(log_file, "[DUMPER] MH_CreateHook rb_iseq_eval thất bại!\n");
        }
    } else {
        if (log_file) fprintf(log_file, "[DUMPER] Không tìm thấy rb_iseq_eval trong export!\n");
    }
    
    if (log_file) fflush(log_file);
}
