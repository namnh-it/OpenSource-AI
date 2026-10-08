# AI Starter — AI Thực Chiến Gateway

Khung backend dùng lại cho các đề thi cần gọi AI Thực Chiến Gateway: text/chat, image, video, TTS, STT, embeddings và moderation. Khung cố ý giữ mỏng: FastAPI + `httpx`, không khóa vào LangChain hay SDK của một nhà cung cấp.

## Khởi động trong 3 phút

```powershell
cd chung-khao/ai-starter
Copy-Item .env.example .env
# điền AITC_API_KEY vào .env (không commit file này)
.\scripts\setup.ps1
.\scripts\run.ps1
```

Mở `http://127.0.0.1:8000/docs` để thử API. Kiểm tra cấu hình trước khi tốn budget:

```powershell
.\.venv\Scripts\python.exe -m app.cli doctor
```

## Cấu trúc

```text
app/
  api/routes.py          # API ổn định cho frontend / demo
  core/config.py         # biến môi trường, model mặc định, quota
  core/gateway.py        # một client chung cho toàn bộ Gateway BTC
  core/artifacts.py      # lưu file media cục bộ và trả URL an toàn
  core/audit.py          # log request-id, model, endpoint, chi phí
  agents/runner.py       # vòng agent có tool allow-list + hard step limit
  schemas.py             # request/response contract
  main.py                # FastAPI app
  cli.py                 # doctor + gọi text nhanh từ terminal
tests/                   # test không gọi API thật
runtime/                 # artefact và audit log (gitignore)
```

## API đã có sẵn

| Mục đích | Endpoint local | Gateway BTC |
| --- | --- | --- |
| Chat/text | `POST /api/ai/text` | `/chat/completions` |
| Sinh ảnh | `POST /api/ai/images` | `/images/generations` |
| Tạo video | `POST /api/ai/videos` | `/v1/videos` |
| Xem trạng thái video | `GET /api/ai/videos/{video_id}` | `/v1/videos/{id}` |
| Tải video hoàn tất | `POST /api/ai/videos/{video_id}/download` | `/v1/videos/{id}/content` |
| TTS / STT | `POST /api/ai/audio/speech`, `/transcriptions` | `/audio/*` |
| Embedding / moderation | `POST /api/ai/embeddings`, `/moderations` | endpoint tương ứng |
| Agent có công cụ | `POST /api/ai/agent/runs` | `/chat/completions` + tool calling |

Ảnh, âm thanh và video được lưu ở `runtime/artifacts/` rồi trả về `artifact_url`; file này được FastAPI phục vụ qua `/artifacts/...`. Không trả base64 lớn vào JSON trừ khi Gateway chỉ trả URL.

## Các nguyên tắc khi vào đề thi

1. Sao chép thư mục này vào project bài làm hoặc dùng trực tiếp; chỉ đổi `.env` và model trong `.env`.
2. Dùng model nhỏ trong lần thử đầu (`gpt-6-luna`, `nano-banana-2-lite`, Veo lite 4 giây); nâng cấp sau khi đã có đánh giá chất lượng.
3. Không gọi video đồng bộ trong luồng UI. Tạo job, polling `/api/ai/videos/{id}`, chỉ tải sau `completed`.
4. `runtime/audit.jsonl` chỉ ghi metadata (không ghi prompt, token hay API key) để kiểm soát model, request id, retry và `x-litellm-response-cost`.
5. Với embeddings/RAG, chốt một model cho cả index và query. Với dữ liệu nhạy cảm, kiểm tra quy chế đề và không đưa khóa API lên frontend.

## Vận hành cuộc thi

- [Runbook 120 phút](docs/RUNBOOK_120_MINUTES.md): cách cắt scope, chia web/AI/QA/demo và dùng AI review code có giới hạn.
- [Model & budget policy](docs/MODEL_AND_BUDGET_POLICY.md): phân bổ 50 USD, model theo mục đích và gate kiểm soát chi phí.
- [Pipeline LLM](docs/LLM_PIPELINE_PLAYBOOK.md): chọn nhanh text, retrieval, image, video, audio hoặc agent cho từng dạng đề.
- Format và verify trước demo: `./scripts/format.ps1`, sau đó `./scripts/verify.ps1`.

## Agent lane: flex đúng mức trong 2 giờ

`POST /api/ai/agent/runs` tạo một vòng **plan → tool → observe → answer** thay vì một chat request đơn lẻ. Khung không dùng LangChain hay framework agent nặng: Gateway nhận `tools`, model chọn tool, backend chỉ chạy tool trong allow-list rồi trả kết quả vào hội thoại. Mỗi run bị chặn ở 1–4 vòng để không treo demo hoặc cháy budget.

Mặc định chỉ có `create_checklist` và `draft_text`. `generate_image` phải được bật tường minh trong `allowed_tools`, do có chi phí và độ trễ. Không có tool ghi file tùy ý, chạy shell, gọi URL tùy ý hay đụng secret.

```powershell
# Demo qua terminal: agent tạo checklist rồi chốt câu trả lời.
.\.venv\Scripts\python.exe -m app.cli agent "Chuẩn bị PoC tư vấn tuyển sinh" --context "User cần so sánh 3 ngành" --steps 2
```

```json
POST /api/ai/agent/runs
{
  "goal": "Tạo nội dung demo cho trợ lý tuyển sinh",
  "context": "Người dùng cần so sánh ba ngành theo sở thích và điểm mạnh.",
  "max_steps": 2,
  "allowed_tools": ["create_checklist", "draft_text"]
}
```

Phần nên nói khi thuyết trình: agent có mục tiêu, trạng thái hội thoại và công cụ bị giới hạn; nó có thể tự chọn một chuỗi hành động nhỏ, trace từng bước và dừng có kiểm soát. Đừng tuyên bố agent “tự trị hoàn toàn”; bản PoC này ưu tiên quan sát được, chi phí thấp và fallback rõ ràng.

## Mở rộng nhanh

- Thêm một provider/endpoint mới vào `GatewayClient`; route chỉ gọi client, không tự chứa HTTP logic.
- Thêm schema trước, sau đó thêm test mock ở `tests/`.
- Với agent, thêm tool vào `app/agents/runner.py`, đặt schema input hẹp, chỉ bật trong `allowed_tools`, rồi bổ sung test mock cho tool-call loop.
- Các prompt template, RAG, queue/background worker hay database là phần đặc thù đề bài: đặt ở `app/features/<ten_bai_toan>/`, không sửa `core/` nếu không cần.

## Các biến môi trường quan trọng

Xem đầy đủ tại `.env.example`. `AITC_API_KEY` là bắt buộc khi gọi thật. Có thể đặt `AI_DRY_RUN=true` để kiểm thử UI/luồng tích hợp mà không phát sinh chi phí; các endpoint AI sẽ trả lỗi hướng dẫn thay vì âm thầm gửi request.
