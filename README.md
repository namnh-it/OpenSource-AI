# OpenSource AI

Kho lưu các khung mã và tài liệu chuẩn bị cho việc xây dựng sản phẩm AI demo.

## Nội dung

- `ai-starter/`: backend FastAPI gọn để gọi AI Thực Chiến Gateway, bao gồm text, ảnh, audio, video, embeddings, moderation và agent có tool allow-list.
- `preparation/handbooks/`: sổ tay chọn model, pipeline ý tưởng và code Gateway.
- `preparation/references/`: tài liệu tham khảo về vòng Chung khảo, API và chiến lược chuẩn bị.
- `preparation/rules/`: bản quy chế dùng để đọc lại.

## Khởi động ai starter

```powershell
cd ai-starter
Copy-Item .env.example .env
# Dien AITC_API_KEY vao .env, khong commit file nay
.\scripts\setup.ps1
.\scripts\run.ps1
```

Sau đó mở `http://127.0.0.1:8000/docs`.

## An toàn khi dùng

- Không commit API key, token AI Log, dữ liệu người dùng hoặc log runtime.
- Chỉ dùng Gateway và công cụ được ban tổ chức cho phép khi tham gia cuộc thi.
- Kiểm tra lại quy chế và tài liệu BTC mới nhất trước khi gọi API thật.
