# Model và budget policy — khung 50 USD

Tài liệu này là **phân bổ kế hoạch**, không phải lệnh tự động được phép chi 50 USD. Trước khi gọi thật, kiểm tra số dư/key của BTC và ghi chi phí từng request từ header `x-litellm-response-cost`. Skill `delivery-review` hiện vẫn yêu cầu tách chi phí authoring khỏi app runtime; không xem số hiển thị của công cụ authoring là bằng chứng chi phí bằng 0.

## Phân bổ trần theo mục đích

| Ngăn chi | Trần kế hoạch | Khi nào được dùng | Không được dùng cho |
| --- | ---: | --- | --- |
| Khảo sát/smoke test | $4 | 1 request/model hoặc test capability | thử prompt ngẫu nhiên |
| AI hỗ trợ lập trình | $6 | triage bug/review diff có test log | đưa cả repo, sửa tự động |
| Runtime lõi cho sản phẩm | $25 | luồng người dùng chính đã chốt | chức năng “hay thì có” |
| Asset demo (ảnh/video/audio) | $7 | đúng asset xuất hiện khi demo | sinh hàng loạt để chọn |
| Dự phòng/final validation | $8 | blocker đã tái lập, test cuối | dùng hết vì còn budget |
| **Tổng** | **$50** |  |  |

Không chuyển tiền từ reserve sang một hạng mục nếu chưa có quyết định của người điều phối. Nếu bài không cần media, giữ ngăn asset làm reserve; nếu cần video, lấy từ ngăn runtime trước, không lấy từ code review.

## Chọn model theo mục đích

| Tác vụ | Model mặc định | Chỉ nâng cấp khi | Tránh |
| --- | --- | --- | --- |
| Code review, triage bug, giải thích test | `gpt-6-luna`, effort `low` | lỗi còn tái lập sau một patch nhỏ → 1 call `gpt-6.1-sol`, `low` | `gpt-6-astra`; dump toàn repo |
| Phân loại/trích xuất/viết lại runtime | `gpt-6-luna`, effort `none` | chất lượng không đạt với fixture đại diện | thinking mặc định khi chỉ cần rule đơn giản |
| Chat cần lý luận có cấu trúc | `gpt-6-luna`, `low` | một yêu cầu trọng yếu không đạt → `gpt-6.1-sol`, `low` | giới hạn completion quá thấp |
| Copy/summarize rẻ | `deepseek-flash`, thinking tắt | cần reasoning thực sự | dùng DeepSeek cho image/audio/web |
| Ảnh demo | SVG/CSS local trước; `gpt-image-2.5-flare` 1024² `low` khi cần | phải giữ đúng style/tỉ lệ → `nano-banana-2-lite` | gọi nhiều ảnh để chọn ngẫu nhiên |
| Video demo | `veo-3.1-lite-generate-001`, 4 giây, 720p | clip đầu pass storyboard nhưng thiếu chất lượng | 8 giây/1080p ngay từ đầu |
| Semantic RAG | `text-embedding-3-small` hoặc `text-multilingual-embedding-002` | chỉ khi có corpus thật cần retrieval | đổi model giữa index và query |

## Cơ sở chi phí và quy tắc gọi

Theo bảng giá BTC kiểm tra ngày 05-10-2026: `gpt-6-luna` là $0.10 input / $0.50 output mỗi 1M token; `gpt-6.1-sol` là $2 / $10; `gpt-6-astra` là $10 / $50. Vì reasoning token cũng tính như output, bảng trên là chỉ dẫn chọn model chứ không phải cam kết chi phí chính xác. Một review 24k ký tự thường chỉ nên là một call nhỏ, nhưng vẫn đặt trần $6 để ngăn một vòng lặp prompt vô hạn.

Với media, `nano-banana-2-lite` khoảng $0.0336/ảnh, còn Veo Lite 720p là $0.05/giây: một clip 4 giây khoảng $0.20. TTS/STT chỉ nên bật nếu nằm trong đường demo; moderation miễn phí nhưng vẫn không thay thế validation nghiệp vụ.

## Các gate bắt buộc

1. Mỗi call phải có mục tiêu kiểm tra được, model, cap và người xác nhận.
2. Gọi smoke test một lần; sau đó xem `runtime/audit.jsonl` và trang quản lý key trước batch/media tiếp theo.
3. Nếu chi phí thực vượt 70% ngăn chi, khóa hạng mục đó và chuyển sang fixture/baseline.
4. Giữ prompt system ổn định để tận dụng cached input; không log prompt/user data vào audit.
5. Trước nộp, ghi `runtime` spend và authoring spend riêng trong `review.md` / `experiment.md`.

Nguồn kỹ thuật: [bảng giá AI Thực Chiến](https://docs.thucchien.ai/docs/round-2/user-guide/pricing) và [hướng dẫn model OpenAI/DeepSeek](https://docs.thucchien.ai/docs/round-2/user-guide/openai-deepseek), kiểm tra ngày 05-10-2026.
