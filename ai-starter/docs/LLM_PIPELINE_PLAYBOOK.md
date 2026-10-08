# Pipeline LLM cho bài thi ngắn

Mục tiêu của pipeline là tạo một hành động người dùng chạy được, có kết quả nhìn thấy và có fallback. Không bắt đầu từ model. Bắt đầu từ quyết định mà người dùng cần thực hiện sau khi nhận kết quả.

## Cách chọn trong 60 giây

1. Viết một câu: **ai làm gì, nhập gì, nhận gì và quyết định gì tiếp theo**.
2. Làm baseline không AI cho đúng câu đó. Baseline có thể là rule, filter, fixture, công thức hoặc template có sẵn.
3. Chỉ chọn một lane AI tạo ra phần giá trị mà baseline chưa làm được.
4. Chọn output nhỏ nhất có thể kiểm tra được: JSON ngắn, một đoạn tư vấn, một ảnh hoặc một video 4 giây.
5. Đặt fallback trước khi gọi model: fixture, kết quả baseline hoặc asset tĩnh.

Quy tắc chọn lane:

| Khi người dùng cần | Lane chính | Không cần làm |
| --- | --- | --- |
| Giải thích, phân loại, tóm tắt, trích xuất, viết lại | Text LLM | Agent, RAG hay video chỉ để trông phức tạp |
| Câu trả lời phải dựa trên tài liệu thật của đề | Embedding và retrieval nhỏ | RAG nếu chưa có corpus hoặc dữ liệu chỉ là vài dòng form |
| Một asset trực quan cho màn hình/slide | Image | Sinh nhiều ảnh để chọn ngẫu nhiên |
| Chuyển động là bản thân giá trị sản phẩm | Video job bất đồng bộ | Video nếu ảnh tĩnh đã chứng minh được luồng |
| Nhập hoặc xuất giọng nói là một phần UX | STT hoặc TTS | Audio khi chỉ để trang trí demo |
| Kết quả tool đầu tiên quyết định bước kế tiếp | Agent có 1–2 tool | Agent cho một câu trả lời đơn lẻ |

## Pipeline chung

```text
User action
  -> validate input + normalize
  -> baseline deterministic
  -> AI lane được chọn
  -> validate output theo contract
  -> render kết quả / lưu artifact
  -> fallback khi lỗi, timeout hoặc vượt ngân sách
  -> audit: model, request id, retry, chi phí
```

Mỗi proposal nên trả lời được bảy ô dưới đây trước khi code:

| Ô cần chốt | Câu hỏi cần trả lời |
| --- | --- |
| User action | Một hành động hoàn chỉnh là gì? |
| Input contract | Các field nào bắt buộc, giới hạn bao nhiêu ký tự/tệp? |
| Baseline | Không gọi AI thì hiển thị hoặc xử lý tối thiểu gì? |
| AI lane | Text, retrieval, image, video, audio hay agent? |
| Output contract | UI nhận chuỗi, JSON, artifact URL hay trạng thái job? |
| Validation | Cần kiểm tra schema, độ dài, policy hay confidence nào? |
| Fallback | Lỗi Gateway thì người dùng vẫn thấy gì? |

`ai-starter` đã có sẵn các endpoint theo từng lane. Route UI chỉ gọi endpoint local; HTTP Gateway, retry, audit và artifact không đi thẳng từ frontend.

## Lane text

Phù hợp nhất cho đa số đề. Luồng nên là:

```text
form hoặc fixture
  -> validate field nghiệp vụ
  -> rule/baseline ngắn
  -> POST /api/ai/text
  -> kiểm tra output có rỗng/quá dài không
  -> card kết quả + lý do + bước tiếp theo
```

Prompt nên có bốn phần: vai trò, dữ kiện được phép dùng, định dạng đầu ra, và điều không được bịa. Dùng nhiệt độ thấp khi cần phân loại/trích xuất; giữ một prompt system ổn định để dễ debug và tận dụng cache. Nếu frontend cần dữ liệu có cấu trúc, yêu cầu JSON trong prompt rồi parse/validate ở backend trước khi hiển thị; không tin JSON model trả về chỉ vì nó trông đúng.

Model khởi đầu: `gpt-6-luna`, reasoning thấp hoặc không bật thinking tùy tác vụ. Chi tiết về budget nằm trong `MODEL_AND_BUDGET_POLICY.md`.

## Lane retrieval

Chỉ thêm retrieval khi câu trả lời phải dựa trên một tập tài liệu thật. Luồng nhỏ nhất:

```text
docs đã chọn
  -> chunk cố định + metadata nguồn
  -> POST /api/ai/embeddings một lần để index
  -> query embedding
  -> top 3 chunks
  -> POST /api/ai/text với chunks + yêu cầu nêu giới hạn
```

Giữ cùng một embedding model cho index và query. Với ít hơn vài trang hoặc chỉ có dữ liệu form, truyền thẳng context vào text prompt sẽ nhanh và đáng tin hơn RAG.

## Lane image

Ảnh là asset, không phải luồng quyết định chính. Luồng nên là:

```text
brief có subject + style + bố cục + tỉ lệ
  -> POST /api/ai/images, n = 1
  -> artifact_url hoặc source_url
  -> preview trong UI
  -> placeholder SVG/CSS nếu lỗi
```

Đầu tiên dùng SVG/CSS hay ảnh có sẵn nếu chúng đã đủ cho demo. Chỉ sinh một ảnh khi asset xuất hiện trong đường demo; không gọi batch để tìm ảnh đẹp. Lưu URL/artifact thay vì base64 trong state frontend.

## Lane video

Video phải là background job. Gửi đúng một clip ngắn sớm, sau đó tiếp tục làm web và AI text trong khi polling.

```text
storyboard 1 cảnh + prompt + 4 giây
  -> POST /api/ai/videos
  -> lưu video_id
  -> polling GET /api/ai/videos/{video_id}
  -> completed: POST /download và render artifact_url
  -> timeout/fail: poster tĩnh + UI trạng thái rõ ràng
```

Không để request video chặn màn hình chính. Nếu tới checkpoint demo mà job chưa xong, dùng poster/placeholder đã chuẩn bị; đừng chạy thêm clip chỉ để may mắn có kết quả tốt hơn.

## Lane speech và transcription

Chỉ dùng khi giọng nói làm giảm rõ ràng số thao tác của user: STT cho input rảnh tay, TTS để đọc kết quả. Luồng là tệp/chuỗi nhỏ -> endpoint audio -> artifact hoặc text -> UI. Luôn giữ input text/button thay thế để có thể demo khi microphone hoặc quyền trình duyệt lỗi.

## Lane agent

Agent chỉ là một extension của text lane khi cần chuỗi hành động phụ thuộc nhau:

```text
goal + context
  -> controller model chọn tool trong allow-list
  -> tool result được ghi vào state
  -> controller trả lời cuối hoặc dừng khi hết bước
```

`POST /api/ai/agent/runs` trong starter giới hạn 1–4 bước. Mặc định agent chỉ có `create_checklist` và `draft_text`; `generate_image` phải bật tường minh. Với demo 2 giờ, đặt `max_steps: 2`, hiển thị `trace` dạng timeline, và để UI vẫn render được `final_answer` nếu model không gọi tool.

## Áp dụng thử theo các hướng từng được ghi chú

Tài liệu tham khảo của đội từng dự đoán bài có tác động xã hội, khả năng thương mại hóa và các hướng EdTech, FinTech, đô thị/logistics hoặc hành chính. Đây là gợi ý để luyện, không phải thông báo đề chính thức.

| Case card | Happy path nên làm | Lane AI | Baseline và fallback |
| --- | --- | --- | --- |
| EdTech: chọn lộ trình học | Người học nhập mục tiêu, thời gian, sở thích; nhận kế hoạch 3 bước có lý do | Text; agent checklist nếu cần tạo kế hoạch nhiều bước | Rule match theo mục tiêu/thời gian; fixture ba lộ trình |
| FinTech: giải thích chi tiêu | Người dùng nhập vài khoản chi; nhận nhóm chi tiêu và câu hỏi để tự rà soát | Rule tổng hợp + text giải thích | Tổng theo nhóm bằng code; không tư vấn đầu tư/tín dụng cá nhân; dữ liệu giả lập khi Gateway lỗi |
| Đô thị/logistics: triage phản ánh | Người dân nhập mô tả sự cố; hệ thống trả category, độ ưu tiên và phiếu tóm tắt | Text classification/extraction | Keyword/rule mapping; nhãn “cần người xác nhận”, không điều khiển hệ thống thật |
| Hành chính: chuẩn bị hồ sơ | User chọn thủ tục và đính kèm mô tả; nhận checklist giấy tờ còn thiếu | Text + retrieval nếu có bộ quy định thật | Checklist tĩnh theo thủ tục; nêu nguồn và thời điểm dữ liệu |

Ví dụ nên luyện trước: **trợ lý chọn lộ trình học**. Web chỉ có một form và một trang kết quả. Backend chạy rule kiểm tra field, gọi `/api/ai/text` để viết giải thích cá nhân hóa, sau đó hiển thị ba bước cùng disclaimer. Nếu muốn cho thấy agent, đổi nút “Tạo lộ trình” thành `/api/ai/agent/runs` với hai tool mặc định; đừng thêm agent nếu text call đã cho kết quả rõ ràng.

## Nhịp triển khai 120 phút

| Mốc | Quyết định pipeline |
| --- | --- |
| 0–16 phút | Chốt user action, output contract, baseline, fallback và đúng một AI lane |
| 16–28 phút | Chạy smoke test một request thật; ghi model, request id và chi phí |
| 28–65 phút | Hoàn thành happy path end-to-end trước; không thêm lane thứ hai |
| 65–83 phút | Test normal, empty, invalid input và Gateway failure; hiển thị fallback |
| 83–108 phút | Chỉ thêm agent/media nếu nó xuất hiện trong demo và có bằng chứng giá trị |
| 108–120 phút | Dừng gọi model mới trừ blocker; đóng gói demo, fixture và câu chuyện trình bày |

## Template điền nhanh trước khi code

```md
User action:
Input contract:
Kết quả user nhìn thấy:
Quyết định tiếp theo của user:
Baseline không AI:
AI lane duy nhất:
Model + max output/call:
Output validation:
Fallback/fixture:
Một câu demo:
```

Nếu chưa điền được “kết quả user nhìn thấy” và “fallback”, chưa gọi model. Nếu agent, image hoặc video không thay đổi câu demo, bỏ nó.
