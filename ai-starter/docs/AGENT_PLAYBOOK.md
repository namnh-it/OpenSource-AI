# Agent lane — demo được trong 2 giờ

## Khi nào đáng bật

Chỉ bật agent nếu sản phẩm cần **làm nhiều hơn một lần trả lời**: phân rã yêu cầu, tạo checklist, tạo một bản nháp rồi chốt output có trace. Nếu giá trị chính chỉ là hỏi–đáp hoặc một lần sinh nội dung, gọi `POST /api/ai/text` sẽ nhanh và đáng tin hơn.

## Pipeline có sẵn

```text
goal + context
      ↓
controller model (tool choice)
      ↓
tool allow-list: checklist | draft_text | image (opt-in)
      ↓
tool result is appended to state
      ↓
final answer or max-step stop
```

`max_steps` mặc định là 2 và tối đa 4. Đây là guardrail, không phải lời hứa agent sẽ hoàn thành mọi mục tiêu.

## Cách demo an toàn

1. Chọn một goal hẹp, ví dụ “tạo checklist onboarding từ bối cảnh người dùng”.
2. Để `allowed_tools` là `create_checklist`, `draft_text`; không bật `generate_image` nếu không thật sự cần asset.
3. Gọi endpoint và đưa `trace` lên UI dạng timeline: tool nào đã gọi, kết quả tóm tắt gì, final answer là gì.
4. Khi model không gọi tool, vẫn hiển thị `final_answer`; đây là fallback hợp lệ, không retry vô hạn.
5. Khi có `max_steps_reached`, thu hẹp goal hoặc tăng tối đa một bước sau khi biết chi phí chấp nhận được.

## Script thuyết trình 20 giây

“Khác chatbot trả lời một lần, agent nhận mục tiêu, tự chọn một công cụ trong danh sách đã giới hạn, quan sát kết quả rồi mới trả lời. Nhờ vậy chúng em có chuỗi hành động minh bạch cho một tác vụ nhỏ, nhưng vẫn giới hạn hai bước để demo ổn định và kiểm soát chi phí.”

## Không làm trong giờ thi

- Không cho agent quyền chạy shell, đọc file tùy ý, gửi mail, gọi URL tùy ý hoặc truy cập secret.
- Không dùng vòng lặp vô hạn, multi-agent, memory/database hoặc queue nếu chúng không phải phần bắt buộc của đề.
- Không thêm tool chỉ để “flex”; mỗi tool phải dẫn tới một output người dùng nhìn thấy được.
