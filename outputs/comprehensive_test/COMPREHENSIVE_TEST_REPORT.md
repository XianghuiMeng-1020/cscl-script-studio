# 全面测试报告 - 所有14个问题 + Initial Idea功能

测试时间: 2026-03-14 23:09:04

测试URL: https://web-production-591d6.up.railway.app/teacher

用户名: teacher_demo

## 测试结果摘要

- **通过**: 4
- **失败**: 8
- **总计**: 12

## 详细结果

### login
**状态**: ✓ PASS

### issue_11_12_sidebar
**状态**: ✓ PASS

### step1_upload
**状态**: ✗ FAIL
**详情**: FAIL: Message: 
Stacktrace:
0   chromedriver                        0x000000010115d6b4 cxxbridge1$str$ptr + 3127600
1   chromedriver                        0x0000000101155a50 cxxbridge1$str$ptr + 3095756
2   chromedriver                        0x0000000100c3256c _RNvCsdExgN8vFLbb_7___rustc35___rust_no_alloc_shim_is_unstable_v2 + 75432
3   chromedriver                        0x0000000100c7b864 _RNvCsdExgN8vFLbb_7___rustc35___rust_no_alloc_shim_is_unstable_v2 + 375200
4   chromedriver                        0x0000000100cba620 _RNvCsdExgN8vFLbb_7___rustc35___rust_no_alloc_shim_is_unstable_v2 + 632668
5   chromedriver                        0x0000000100c6fb9c _RNvCsdExgN8vFLbb_7___rustc35___rust_no_alloc_shim_is_unstable_v2 + 326872
6   chromedriver                        0x000000010111c680 cxxbridge1$str$ptr + 2861308
7   chromedriver                        0x000000010111fdd4 cxxbridge1$str$ptr + 2875472
8   chromedriver                        0x0000000101101a7c cxxbridge1$str$ptr + 2751736
9   chromedriver                        0x0000000101120658 cxxbridge1$str$ptr + 2877652
10  chromedriver                        0x00000001010f1ffc cxxbridge1$str$ptr + 2687608
11  chromedriver                        0x0000000101144d78 cxxbridge1$str$ptr + 3026932
12  chromedriver                        0x0000000101144ef4 cxxbridge1$str$ptr + 3027312
13  chromedriver                        0x00000001011556a8 cxxbridge1$str$ptr + 3094820
14  libsystem_pthread.dylib             0x0000000185e1ec0c _pthread_start + 136
15  libsystem_pthread.dylib             0x0000000185e19b80 thread_start + 8


### initial_idea
**状态**: ✗ FAIL
**详情**: FAIL: Message: 


### issue_4_button_i18n
**状态**: ✓ PASS

### issue_8_output_tabs
**状态**: ✗ FAIL
**详情**: FAIL: 只找到0个标签页

### issue_7_no_pipeline_summary
**状态**: ✓ PASS

### issue_5_edit_regenerate
**状态**: ✗ FAIL
**详情**: FAIL: 找不到按钮

### issue_6_export_labels
**状态**: ✗ FAIL
**详情**: FAIL: 找不到导出按钮

### issue_9_quality_report
**状态**: ✗ FAIL
**详情**: FAIL: 找不到质量报告链接

### issue_10_course_documents
**状态**: ✗ FAIL
**详情**: FAIL: 找不到课程文档链接

### issue_13_edit_duplicate
**状态**: ✗ FAIL
**详情**: FAIL: 找不到活动项目链接
