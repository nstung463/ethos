# Security Review và Roadmap

## Phát hiện chính

1. Critical: Backend trước đây không có authentication/authorization thực sự nhưng lại có nguy cơ được deploy như public web app. Khi các route `v1`, `files`, `terminals` bị mở ra mà không có identity + ownership model, bất kỳ ai biết URL đều có thể gọi chat, upload file, hoặc đụng vào sandbox.

2. Critical: Terminal/file proxy có thể vô tình biến credential của server thành quyền public gián tiếp. Nếu không có authz theo user và ownership check, anonymous caller có thể dùng quyền sandbox/backend của server.

3. Critical: `session_id` do client tự gửi không nên được dùng làm identity cho state hoặc sandbox. Nếu server trust giá trị này, người khác có thể reuse state/sandbox hoặc tạo vô hạn sandbox mới để abuse tài nguyên.

4. High: API key hiện vẫn có thể nằm ở browser và được gửi raw xuống backend theo từng request. Mô hình này không đủ chuẩn production vì XSS, extension độc hại, máy dùng chung, hoặc browser compromise đều có thể làm lộ key.

5. High: Có SSRF surface nếu client được phép gửi `base_url` hoặc Azure endpoint tùy ý và backend dùng trực tiếp giá trị đó để gọi ra ngoài.

6. High: Managed files nếu là global và không có ownership/ACL sẽ cho phép caller khác list/search/read/update/delete file của user khác. `GET /api/files/all` là điểm nguy hiểm nhất của lớp này.

7. Medium: Nếu dùng local sandbox thì boundary host filesystem không còn đúng cho môi trường internet-facing. Local mode chỉ phù hợp cho development hoặc môi trường được kiểm soát chặt.

8. Medium: Tool arguments hoặc nội dung reasoning nếu stream thẳng ra UI có thể làm lộ secret, token, path nhạy cảm, hoặc thông tin nội bộ.

## Roadmap

### 0-7 ngày

- Chặn public access ngay: đặt backend sau VPN, basic auth, hoặc reverse proxy có auth.
- Tắt hoàn toàn `/api/terminals/*` và `/api/files/*` khỏi internet cho tới khi có auth + ACL.
- Rotate toàn bộ `OPEN_TERMINAL_API_KEY`, `DAYTONA_API_KEY`, fallback provider keys; nếu `.env` từng chia sẻ nội bộ thì rotate luôn.
- Bỏ `allow_origins=["*"]`, thay bằng allowlist cụ thể.
- Thêm rate limit/IP throttling cho `/v1/chat/completions`, upload, terminals.

### 1-2 tuần

- Thêm user auth thực sự: session/JWT/OIDC.
- Gắn mọi chat/file/sandbox với `user_id`; mọi route phải check ownership.
- Không trust `session_id` từ client nữa. Server tự sinh opaque session/thread id và map nội bộ.
- Xóa `GET /api/files/all`; thay bằng list file theo user.
- Chặn hoặc allowlist `base_url`/Azure endpoint; tốt nhất tắt custom endpoint ở public mode.

### 2-4 tuần

- Chuyển secret handling sang server-side secure storage hoặc vault.
- Nếu muốn BYOK: chỉ cho local-only mode, hoặc dùng token ngắn hạn/proxy token, không persist raw key trong `localStorage`.
- Redact secrets khỏi logs, SSE, tool previews.
- Thêm resource abuse controls theo user: số request, số terminal/thread create, upload size limits, tổng dung lượng file.
- Thêm audit log bảo mật: ai tạo sandbox nào, upload file nào, dùng model nào, lỗi auth nào.

### 4-8 tuần

- Thiết kế RBAC/scopes rõ ràng:
  - `chat:run`
  - `files:read/write`
  - `terminal:access`
  - `admin:providers`
- Bổ sung retention policy cho files/conversations, secure delete, malware scan nếu cho upload public.
- Thêm security tests: authz tests, file ownership tests, SSRF tests, rate-limit tests.

## Kết luận

Nếu dự án này đang public hoặc sắp public, trạng thái an toàn hiện tại đã tốt hơn nhiều so với prototype ban đầu nhưng vẫn chưa đủ mức production hoàn chỉnh. Các phần đã được vá chủ yếu tập trung vào identity tối thiểu, ownership, route protection, CORS, rate limiting, và giảm bớt bề mặt abuse ở chat/files/terminals. Phần còn lại lớn nhất là secret boundary, auditability, và auth production-grade.

## Khi nÃ o báº¯t buá»™c pháº£i lÃªn database

Hiá»‡n táº¡i project chÆ°a dÃ¹ng database Ä‘Ãºng nghÄ©a. CÃ¡c state chÃ­nh Ä‘ang nÆ°Æ¡ng vÃ o file JSON local:

- auth sessions/users trong `src/app/modules/auth/repository.py`
- threads trong `src/app/services/thread_store.py`
- managed files metadata trong `src/app/services/file_store.py`

MÃ´ hÃ¬nh nÃ y váº«n cháº¥p nháº­n Ä‘Æ°á»£c cho prototype, demo ná»™i bá»™, hoáº·c single-instance deployment. Tuy nhiÃªn, nÃ³ sáº½ trá»Ÿ thÃ nh Ä‘iá»ƒm ngháº½n báº¯t buá»™c pháº£i thay khi chạm báº¥t ká»³ ngÆ°á»¡ng nÃ o sau Ä‘Ã¢y:

### 1. Khi khÃ´ng cÃ²n single-process hoáº·c single-instance

- ChÆ¡y nhiá»u worker backend.
- ChÆ¡y nhiá»u container/instance sau load balancer.
- Cáº§n state nháº¥t quÃ¡n qua restart/redeploy.

LÃºc Ä‘Ã³ file JSON khÃ´ng cÃ²n Ä‘á»§ tin cáº­y vÃ¬ khÃ³ Ä‘áº£m báº£o atomic write, cross-process locking, vÃ  consistency. In-memory rate limit vÃ  local file stores cÅ©ng khÃ´ng cÃ²n Ä‘Ãºng behavior khi scale ngang.

### 2. Khi auth/session trá»Ÿ thÃ nh chÆ°ác nÄƒng nghiÃªm tÃºc

- Cáº§n session expiry.
- Cáº§n revoke/logout.
- Cáº§n audit trail cho login/session.
- Cáº§n support user tháº­t thay vÃ¬ guest session táº¡m.

Auth state lÆ°u plaintext trong file cÃ³ thá»ƒ dÃ¹ng cho prototype, nhÆ°ng khÃ´ng phÃ¹ há»£p cho production-grade identity. Database lÃ  mốc gáº§n nhÆ° báº¯t buá»™c tá»« thÃời Ä‘iá»ƒm muá»‘n nÃ¢ng auth lÃªn má»©c nghiÃªm tÃºc.

### 3. Khi multi-user trá»Ÿ thÃ nh use case chÃ­nh

- User count tÄƒng.
- Cáº§n list/filter/search/paginate theo user, thread, file.
- Cáº§n ownership constraints, uniqueness, retention, soft delete.
- Cáº§n tránh orphaned state hoáº·c corruption khi ghi song song.

Khi Ä‘Ã³, database khÃ´ng chá»‰ lÃ  chuyá»‡n hiá»‡u nÄƒng mÃ  cÃ²n lÃ  data integrity vÃ  security boundary.

### 4. Khi cÃ³ yÃªu cáº§u váº­n hÃ nh production

- Backup/restore chuáº©n.
- Migration schema cÃ³ kiá»ƒm soÃ¡t.
- Encryption at rest / secret rotation / incident response.
- Truy váº¥n audit khi cÃ³ security issue.

File JSON local khÃ´ng phÃ¹ há»£p cho cÃ¡c nhu cáº§u váº­n hÃ nh nÃ y.

### 5. Khi hiá»‡u nÄƒng truy váº¥n báº¯t Ä‘áº§u lÃ  váº¥n Ä‘á»

- Má»—i request pháº£i Ä‘á»c cáº£ file rá»“i lá»c trong memory.
- Dá»¯ liá»‡u thread/file/session tÄƒng dáº§n.
- Cáº§n cleanup job, expiry job, usage accounting, hoáº·c search linh hoáº¡t.

ÄÃ¢y lÃ  dáº¥u hiá»‡u project Ä‘Ã£ vÆ°á»£t khá»i kháº£ nÄƒng an toÃ n vÃ  váº­n hÃ nh cá»§a file-based store.

### Káº¿t luáº­n kiáº¿n trÃºc

Project nÃ y chÆ°a báº¯t buá»™c lÃªn database náº¿u váº«n á»Ÿ má»©c prototype, local/dev, hoáº·c demo ná»™i bá»™. NhÆ°ng náº¿u má»¥c tiÃªu lÃ  production thÃ­t, nhiá»u user, auth nghiÃªm tÃºc, vÃ  cÃ³ kháº£ nÄƒng scale hÆ¡n 1 instance, thÃ¬ database cho `users`, `sessions`, `threads`, `managed_files metadata` lÃ  hÆ°á»›ng di chuyá»ƒn gáº§n nhÆ° báº¯t buá»™c.

Khuyáº¿n nghá»‹:

- ChÆ°a cáº§n dá»i toÃ n bá»™ ngay láº­p tá»©c náº¿u Ä‘ang á»Ÿ giai Ä‘oáº¡n prototype.
- NÃªn coi Postgres cho `users/sessions/threads/files` lÃ  P1 kiáº¿n trÃºc náº¿u roadmap cÃ³ production.
- Redis nÃªn Ä‘i cÃ¹ng P1/P2 cho rate limiting vÃ  ephemeral abuse controls khi báº¯t Ä‘áº§u scale ngang.

## Implementation status checklist

### 0-7 ngày

- `todo` Chặn public access ngay: đặt backend sau VPN, basic auth, hoặc reverse proxy có auth.
- `partial` Tắt hoàn toàn `/api/terminals/*` và `/api/files/*` khỏi internet cho tới khi có auth + ACL.  
  Hiện app đã có auth + ownership check cho files và terminals, nhưng chưa có tầng reverse proxy/network để chặn riêng internet-facing exposure.
- `todo` Rotate toàn bộ `OPEN_TERMINAL_API_KEY`, `DAYTONA_API_KEY`, fallback provider keys; nếu `.env` từng chia sẻ nội bộ thì rotate luôn.
- `done` Bỏ `allow_origins=["*"]`, thay bằng allowlist cụ thể.  
  Backend hiện mặc định chỉ allow origin dev cụ thể qua cấu hình `ETHOS_CORS_ALLOW_ORIGINS`, không còn wildcard mặc định.
- `done` Thêm rate limit/IP throttling cho `/v1/chat/completions`, upload, terminals.  
  Đã thêm limiter cho guest session create, chat requests, thread create, file write/import, terminal create, terminal websocket connect. Hiện limiter là in-memory ở app layer.

### 1-2 tuần

- `partial` Thêm user auth thực sự: session/JWT/OIDC.  
  Hiện đã có guest bearer session + `/auth/guest` + `/auth/me`, đủ để buộc identity trong app; chưa phải OIDC/JWT production-grade.
- `done` Gắn mọi chat/file/sandbox với `user_id`; mọi route phải check ownership.
- `done` Không trust `session_id` từ client nữa. Server tự sinh opaque session/thread id và map nội bộ.
- `done` Xóa `GET /api/files/all`; thay bằng list file theo user.
- `done` Chặn hoặc allowlist `base_url`/Azure endpoint; tốt nhất tắt custom endpoint ở public mode.

### 2-4 tuần

- `todo` Chuyển secret handling sang server-side secure storage hoặc vault.
- `todo` Nếu muốn BYOK: chỉ cho local-only mode, hoặc dùng token ngắn hạn/proxy token, không persist raw key trong `localStorage`.
- `partial` Redact secrets khỏi logs, SSE, tool previews.  
  Đã bỏ args preview khỏi tool reasoning stream; chưa có secret redaction framework đầy đủ cho logs/SSE/toàn bộ tool outputs.
- `partial` Thêm resource abuse controls theo user: số request, số terminal/thread create, upload size limits, tổng dung lượng file.  
  Đã có rate limit và file size/storage caps. Chưa có audit-backed usage accounting hoặc active-resource caps phức tạp hơn.
- `todo` Thêm audit log bảo mật: ai tạo sandbox nào, upload file nào, dùng model nào, lỗi auth nào.

### 4-8 tuần

- `todo` Thiết kế RBAC/scopes rõ ràng:
  - `todo` `chat:run`
  - `todo` `files:read/write`
  - `todo` `terminal:access`
  - `todo` `admin:providers`
- `todo` Bổ sung retention policy cho files/conversations, secure delete, malware scan nếu cho upload public.
- `partial` Thêm security tests: authz tests, file ownership tests, SSRF tests, rate-limit tests.  
  Đã có test cho auth-required task endpoints, file ownership, removal của `/api/files/all`, import ownership, terminal HTTP/websocket authz, và rate-limit/file-size controls. Chưa có SSRF coverage và security test sâu cho infra boundary.
