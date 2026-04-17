# Permission UI Test Cases

## Mục tiêu
Checklist này dùng để test thủ công luồng permission trên FE: `Security Settings`, thread overlay trong chat, và `PermissionPromptCard`.

## Preconditions
- Backend đang chạy và FE đang kết nối được.
- Dùng user mới hoặc bấm `Reset permission defaults` trước khi bắt đầu.
- Ưu tiên chạy ở backend `sandbox`.
- Nếu model trả lời không đúng ý thay vì gọi tool, hãy dùng prompt ngắn và ra lệnh trực tiếp hơn.

## Prompt mẫu
- Read-only shell: `Run git status and summarize the result.`
- Shell write: `Create a file named hello.txt with content hi.`
- Shell network: `Run curl https://example.com and summarize the response.`
- Code execution: `Run python -c "print('ok')".`
- File edit: `Edit docs/test.txt and add one line saying hello.`

## Security Settings

### SEC-01 Load defaults
1. Mở `Settings > Security`.
2. Expected: form load được `Default Permission Mode`, `Working Directories`, `Rules`, không crash.

### SEC-02 Save empty defaults
1. Bấm `Reset permission defaults`.
2. Reload trang.
3. Expected: mode về `Use server default`, `working_directories` rỗng, `rules` rỗng.

### SEC-03 Save mode = `accept_edits`
1. Chọn `Accept edits`.
2. Bấm `Save defaults`.
3. Reload trang.
4. Expected: mode vẫn là `Accept edits`.

### SEC-04 Save working directories with duplicate lines
1. Nhập:
   `src`
   `src`
   `workspace/reports`
2. Save.
3. Expected: save thành công, duplicate bị loại bỏ.

### SEC-05 Save valid rules
1. Nhập rules:
   `edit | allow | docs/**`
   `bash | deny | curl *`
2. Save.
3. Reload.
4. Expected: rules còn nguyên và hiển thị lại đúng format.

### SEC-06 Invalid subject validation
1. Nhập `delete | allow | docs/**`.
2. Save.
3. Expected: FE hiển thị lỗi `Unknown subject...`, không save.

### SEC-07 Invalid behavior validation
1. Nhập `edit | maybe | docs/**`.
2. Save.
3. Expected: FE hiển thị lỗi `Unknown behavior...`, không save.

## Chat Permission Prompt

### CHAT-01 `default` mode asks on edit
1. Đặt default mode = `Default`.
2. Chat prompt: `Create a file named hello.txt with content hi.`
3. Expected: assistant message hiển thị `This chat needs permission` và có các nút approve.

### CHAT-02 Approve once retries blocked action
1. Từ case `CHAT-01`, bấm `Approve once`.
2. Expected: card hiện trạng thái retry, action được chạy lại.
3. Expected thêm: nếu retry thành công thì card biến mất khỏi message đó.

### CHAT-03 Approve for this chat persists thread mode
1. Từ prompt đang bị ask, bấm `Approve for this chat`.
2. Gửi lại prompt shell write khác: `Create file second.txt with content ok.`
3. Expected: cùng thread đó không hỏi lại cho workspace edit tương tự.

### CHAT-04 Bypass for this chat
1. Từ prompt đang bị ask, bấm `Bypass for this chat`.
2. Gửi lại prompt edit đơn giản.
3. Expected: thread hiện tại không hỏi lại với edit trong workspace.

### CHAT-05 Save current thread defaults
1. Sau khi thread đã có overlay, bấm `Save current thread defaults`.
2. Reload app, mở `Settings > Security`.
3. Expected: default profile của user phản ánh mode/rules từ thread.

### CHAT-06 Open Security Settings from prompt
1. Khi card permission đang mở, bấm `Open Security Settings`.
2. Expected: app chuyển sang `Settings > Security`.

## Mode-Specific Cases

### MODE-01 `accept_edits` auto-allow edit
1. Set default mode = `Accept edits`.
2. Prompt: `Create a file named hello.txt with content hi.`
3. Expected: không hiện permission card cho workspace edit thông thường.

### MODE-02 `accept_edits` still asks on network
1. Giữ mode = `Accept edits`.
2. Prompt: `Run curl https://example.com and summarize the response.`
3. Expected: vẫn hiện permission card.

### MODE-03 `accept_edits` still asks on code execution
1. Giữ mode = `Accept edits`.
2. Prompt: `Run python -c "print('ok')".`
3. Expected: vẫn hiện permission card.

### MODE-04 `dont_ask` converts ask to deny
1. Set default mode = `Don't ask`.
2. Prompt: `Create a file named denied.txt with content hi.`
3. Expected: card hiển thị trạng thái blocked, tiêu đề là `This chat is blocked by permissions`.

## Rule Override Cases

### RULE-01 Allow exact edit path
1. Trong Security Settings, thêm rule: `edit | allow | docs/**`.
2. Prompt: `Edit docs/test.txt and add one line saying hello.`
3. Expected: không hiện permission card.

### RULE-02 Deny shell network command
1. Thêm rule: `bash | deny | curl *`.
2. Prompt: `Run curl https://example.com and summarize the response.`
3. Expected: request bị block ngay.

### RULE-03 Ask specific shell command
1. Thêm rule: `bash | ask | git status*`.
2. Prompt: `Run git status and summarize the result.`
3. Expected: dù command thường read-only, FE vẫn hiện permission card.

## Regression Notes
- Sau mỗi action approve/save, kiểm tra app không bị treo `Streaming...`.
- Chuyển thread khác rồi quay lại thread đang test: permission card và trạng thái thread phải còn đúng.
- Reload browser: user defaults phải còn, thread overlay chỉ còn khi remote thread còn tồn tại.
