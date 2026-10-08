# Runbook 120 phút — từ đề đến demo

Mục tiêu không phải là “xong nhiều tính năng”, mà là có một lát cắt chạy được, dễ demo, có fallback và bằng chứng kiểm tra. Runbook này bám chuỗi skill của đội: `brief → solution → technical → coding → delivery review`.

## Luật cắt scope

- Mỗi bài chỉ chọn **một hành động người dùng hoàn chỉnh**: nhập/chọn dữ liệu → xử lý → kết quả có ích → lỗi rõ ràng.
- Có baseline không AI trước: fixture, rule, tìm kiếm thường hoặc kết quả mẫu. AI chỉ dùng cho năng lực baseline không làm được.
- Không thêm tính năng mới sau phút 80. Khi Gateway lỗi, demo phải chuyển sang fixture/baseline thay vì treo UI.
- Không mở nhiều luồng video/ảnh tốn phí cùng lúc. Với video, chạy job đầu tiên sớm rồi làm việc khác trong lúc polling.

## Timeline một nhóm 3 người

| Phút | Kết quả bắt buộc | Web / product | AI / data | Điều phối, bằng chứng |
| --- | --- | --- | --- | --- |
| 0–8 | `brief.md` ngắn | Luồng người dùng, tiêu chí chấm | Kiểm tra input/model khả dụng | Chốt unknown và 1 giả định đảo được |
| 8–16 | `solution.md` 1 lát cắt | Wireframe thô, input/output | Baseline + schema kết quả | Must-have / out-of-scope |
| 16–28 | khung chạy local | Scaffold, route, health | Smoke test một request thật tối đa | Ghi model, chi phí, request-id |
| 28–65 | happy path end-to-end | UI, validation, trạng thái lỗi | Tích hợp đúng **một** năng lực AI | Tạo fixture/fallback, test API |
| 65–83 | có thể demo | Polish đường chính, responsive | So sánh với baseline, giới hạn chi phí | Test normal/empty/failure |
| 83–96 | lỗi lớn đã triage | Sửa lỗi có bằng chứng | 1–2 AI review nhỏ, không sửa tự động | Chạy verify, lưu ảnh/chứng cứ |
| 96–108 | câu chuyện demo | Demo 60–90 giây | Chỉ tạo asset thật sự cần | Viết README, experiment/pitch |
| 108–120 | gói nộp an toàn | Không thêm tính năng | Không gọi model mới trừ blocker | Delivery review, secrets, run lại |

Tỷ trọng năng lực (tổng 120 phút) là **45 phút web/product**, **35 phút AI/backend/data**, **20 phút QA & fallback**, **15 phút demo/tài liệu**, và **5 phút buffer**. Ba người làm song song nhưng mốc kiểm tra vẫn là chung: không để phần web chờ “AI hoàn hảo”.

### Nhánh khi đề cần video

Ở phút 28, gửi đúng một clip 4 giây với `veo-3.1-lite-generate-001`, lưu `video_id`, rồi polling 10 giây/lần ở background. Đến phút 65 chưa hoàn tất hoặc chưa đạt chất lượng: demo bằng placeholder/ảnh tĩnh và mô tả video như một khả năng đã tách job, không chạy thêm clip để “cầu may”.

## Checkpoint ra quyết định

| Thời điểm | Câu hỏi | Nếu câu trả lời là “không” |
| --- | --- | --- |
| Phút 16 | Có thể chạy local và test một input không? | Bỏ framework thừa, về starter nhỏ hơn. |
| Phút 45 | Người dùng có nhận kết quả nhìn thấy được không? | Cắt mọi tính năng phụ, hoàn thiện happy path. |
| Phút 80 | Baseline + fallback + test lỗi có chưa? | Dừng polish/asset; hoàn thiện độ tin cậy. |
| Phút 108 | Có thể run từ terminal mới và demo dưới 90 giây? | Không thêm AI call mới; chỉ sửa blocker. |

## AI hỗ trợ code: quy trình 12 phút tối đa

1. Chạy test hoặc tái lập lỗi trước; ghi đúng command, lỗi và file nghi vấn.
2. Chỉ gửi một file/diff tập trung (tối đa 24k ký tự), tiêu chí chấp nhận và log lỗi. Không gửi `.env`, token, ảnh dump lớn hay toàn repo.
3. Dùng `gpt-6-luna`, `reasoning_effort=low`, nhận tối đa 5 phát hiện và patch plan.
4. Con người áp dụng patch nhỏ, chạy `scripts/verify.ps1`; không chấp nhận sửa chỉ vì model nói đúng.
5. Chỉ khi vẫn còn blocker tái lập mới gọi `gpt-6.1-sol` một lần với cùng scope và log mới. Không dùng `gpt-6-astra` trong hackathon 2 giờ.

Lệnh đã chuẩn bị:

```powershell
.\scripts\ai-review.ps1 -File app\api\routes.py -Mode debug -Context "POST /api/ai/images returns 502 with this fixture..."
.\scripts\verify.ps1
```

Đây là review có giới hạn, không phải lệnh tự sửa code. Script từ chối file secret phổ biến; người dùng vẫn chịu trách nhiệm không gửi dữ liệu nhạy cảm.
