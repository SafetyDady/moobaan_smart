# Table View Design Specification - ประวัติการส่งสลิป

## Overview
การออกแบบใหม่สำหรับส่วน "ประวัติการส่งสลิป" ในหน้า Mobile Dashboard โดยเปลี่ยนจาก Card-based UI เป็น Table View เพื่อแสดงข้อมูลได้มากขึ้นในพื้นที่เดียวกัน

---

## Table Structure

### Column Headers
| Column | Header Text | Width | Alignment |
|--------|-------------|-------|-----------|
| 1 | จำนวนเงิน | 20% | Left |
| 2 | วันที่-เวลา | 30% | Left |
| 3 | สถานะ | 25% | Center |
| 4 | แอคชั่น | 25% | Right |

### Table Styling
```css
/* Container */
background: #1e293b (Gray 800)
border-radius: 8px
padding: 0
overflow: hidden

/* Header Row */
background: #334155 (Gray 700)
padding: 12px 8px
font-size: 12px
font-weight: 600
color: #9ca3af (Gray 400)
text-transform: none

/* Data Rows */
background: #1e293b (Gray 800)
border-bottom: 1px solid #334155 (Gray 700)
padding: 12px 8px
min-height: 60px

/* Alternating Rows (Optional) */
nth-child(even): background: #1a2332 (Slightly darker)

/* Last Row */
border-bottom: none
```

---

## Row Data Structure

### Column 1: จำนวนเงิน (Amount)
```
฿{amount}
```
- Font size: 18px (Bold)
- Color: #ffffff (White)
- Format: ฿{number with commas}
- Example: ฿700, ฿3,500, ฿10,000

### Column 2: วันที่-เวลา (Date-Time)
```
{date} {time}
```
- Font size: 14px (Regular)
- Color: #d1d5db (Gray 300)
- Format: {day} {month_abbr}. {year} {HH:MM}
- Example: 1 ม.ค. 69 11:11, 15 ธ.ค. 68 14:30

### Column 3: สถานะ (Status)
Status badge with rounded corners:

| Status | Text | Background | Text Color |
|--------|------|------------|------------|
| PENDING | รอตรวจสอบ | #eab308 (Yellow 500) | #000000 (Black) |
| SUBMITTED | รอตรวจสอบ | #3b82f6 (Blue 500) | #ffffff (White) |
| ACCEPTED | ยืนยันแล้ว | #10b981 (Green 500) | #ffffff (White) |
| REJECTED | ถูกปฏิเสธ | #ef4444 (Red 500) | #ffffff (White) |
| REJECTED_NEEDS_FIX | ต้องแก้ไข | #ef4444 (Red 500) | #ffffff (White) |
| DRAFT | ร่าง | #6b7280 (Gray 500) | #ffffff (White) |

Badge styling:
```css
padding: 4px 12px
border-radius: 12px
font-size: 12px
font-weight: 600
white-space: nowrap
```

### Column 4: แอคชั่น (Actions)
Icon buttons displayed horizontally:

**View Button (👁️ ดูรายละเอียด):**
```css
background: #374151 (Gray 700)
width: 36px
height: 36px
border-radius: 50%
display: flex
align-items: center
justify-content: center
```
- Icon: Eye (👁️) or `<svg>` eye icon
- Color: #ffffff (White)
- Always visible for all statuses

**Edit Button (✏️ แก้ไข):**
```css
background: #3b82f6 (Blue 500)
width: 36px
height: 36px
border-radius: 50%
display: flex
align-items: center
justify-content: center
margin-left: 8px
```
- Icon: Pencil (✏️) or `<svg>` edit icon
- Color: #ffffff (White)
- Visible only when editable (DRAFT, PENDING, REJECTED, REJECTED_NEEDS_FIX)

**Button Spacing:**
- Gap between buttons: 8px
- Buttons aligned to the right

---

## Responsive Behavior

### Mobile (< 640px)
- Table scrolls horizontally if needed
- Minimum column widths maintained
- Touch targets: 44px × 44px minimum

### Tablet (640px - 1024px)
- Table fits full width
- Columns expand proportionally

---

## Accessibility

### Touch Targets
- All buttons: 36px × 36px (within 44px tap area with padding)
- Row height: minimum 60px
- Column padding: 8px

### Color Contrast
- Text vs Background: WCAG AA compliant
- Status badges: High contrast
- Icons: White on colored backgrounds

---

## Empty State
When no payment history:
```
ไม่มีประวัติการส่งสลิป
กดปุ่ม + ด้านล่างเพื่อส่งสลิปใหม่
```
- Text color: #6b7280 (Gray 500)
- Center aligned
- Padding: 40px

---

## Loading State
```
กำลังโหลดข้อมูล...
```
- Spinner icon
- Center aligned
- Padding: 40px

---

## Interaction States

### Row Hover (Desktop)
```css
background: #2d3748 (Lighter gray)
cursor: pointer
transition: background 0.2s ease
```

### Button Hover
```css
opacity: 0.8
transition: opacity 0.2s ease
```

### Button Active
```css
transform: scale(0.95)
transition: transform 0.1s ease
```

---

## Implementation Notes

1. **Horizontal Scroll:** Use `overflow-x: auto` on table container for mobile
2. **Sticky Header:** Optional - make header row sticky on scroll
3. **Row Click:** Entire row clickable to view details (optional)
4. **Icon Library:** Use existing icon library (e.g., Heroicons, Lucide)
5. **Status Mapping:** Reuse existing status constants from code

---

## Comparison: Card vs Table

| Aspect | Card View | Table View |
|--------|-----------|------------|
| Space Efficiency | Low (1-2 items visible) | High (3-4 items visible) |
| Scanability | Medium | High |
| Information Density | Low | High |
| Mobile Friendly | Very High | High |
| Touch Targets | Large | Medium |
| Visual Hierarchy | Strong | Moderate |

**Recommendation:** Table View เหมาะสำหรับผู้ใช้ที่ต้องการดูข้อมูลหลายรายการพร้อมกัน และเปรียบเทียบข้อมูล

