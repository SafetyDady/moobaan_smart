# ผลแก้ตาม Auditor: ตารางใบแจ้งหนี้ลูกบ้าน — 11 กันยายน 2026

สถานะ: แก้และทดสอบในเครื่องเสร็จ ยังไม่ commit/push/deploy ไม่เชื่อมต่อ production หรือ DB ในการทดสอบ UI รอบนี้

**อัปเดตการอนุมัติ:** เจ้าของสั่ง “OK Push ได้” แล้ว กำลังเตรียมเผยแพร่พร้อมbackup DB/restoreตรวจ26ตารางและตรวจค่าseed/resetก่อนpush. จุดย้อนกลับเฉพาะcodeคือ `3c1bbb68a546218ad943131b8a458bd04057130d`; ผลdeploymentจะบันทึกหลังตรวจเสร็จ ข้อความที่ระบุlocalonlyในรายงานด้านล่างเป็นผลในขั้นทดสอบก่อนอนุมัติ

## ปิดข้อสังเกต P3 เรื่องสีหลัง Auditor รับรอง

เจ้าของอนุมัติให้ดำเนินการตามข้อเสนอ: แยก ISSUED/“ค้างชำระ” เป็น slate (border-slate-500, text-slate-300, badge bg-slate-700/text-slate-200) โดยคง PARTIALLY_PAID เป็น amber, CREDITED เป็น sky และ PAID เป็น emerald. PENDING เดิมยังเหลืองและแยกcaseออกจากISSUED. ไม่เปลี่ยนข้อความ/ลำดับบิลพิเศษ/ตรรกะอื่น

หลังแก้สีรันbrowser29+nativeinput5ซ้ำผ่าน34/34และbuild/diffcheckผ่าน; ตรวจภาพ360/390/768และcomputedcolorsแล้ว ค้างชำระbadgeพื้นrgb(51,65,85) ตัวอักษรrgb(226,232,240) ต่างจากชำระบางส่วนพื้นrgba(120,53,15,0.3) ตัวอักษรrgb(251,191,36). หลักฐานล่าสุด `slate-results.json`, `slate-colors.json`, `slate-360-left.png`, `slate-390-right.png`, `slate-768-left.png` ในแฟ้มทดสอบเดิม; native-scroll-results.json เป็นผลรันซ้ำล่าสุด. ชุดยังอยู่ในเครื่อง ยังไม่commit/push/deploy

## ขอบเขตสุดท้าย

1. ตาราง Resident Dashboard ใช้ “ค้างชำระ” สำหรับ ISSUED, “ชำระบางส่วน” สำหรับ PARTIALLY_PAID, “ลดหนี้แล้ว” สำหรับ CREDITED พร้อมสี amber/sky ที่แยกจากชำระแล้ว
2. เพิ่ม “ชำระล่าสุด” จาก API paid_at เดิม แสดงวันที่+เวลาไทยสองบรรทัด ไม่มีการชำระแสดง `-`; ไม่ใช้สลิปรอตรวจหรือ applied_at
3. วันที่ครบกำหนดและวันที่ชำระใช้ shared Bangkok formatters; ลบ formatter local timezone และ fallback created_at.slice(0,10) ที่ไม่จำเป็น เพราะ API มี due_date
4. เรียงสำเนาข้อมูลใหม่→เก่า ตามรอบบิลรายเดือน; บิลพิเศษใช้ due_date; วันที่เท่ากันใช้ ID descending ไม่เปลี่ยน props ต้นฉบับ ไม่ใช้วันที่สร้างย้อนหลังมาแซงรอบบิล
5. ตาราง max-height384px, min-width520px, scrollสองทิศทาง, sticky header, keyboard-focusable labelled region; gridสุดท้าย **2+3+2+2+3** เพิ่มพื้นที่จำนวนเงิน
6. เพิ่ม onTouchCancel ใน PullToRefresh ให้ล้างสถานะ/พิกัดท่าลากที่ยกเลิก ไม่เรียก refresh จากการแตะครั้งต่อไป และไม่ยกเลิกงาน refresh ที่กำลังทำอยู่

ไฟล์โปรแกรมที่เปลี่ยน:
- `frontend/src/pages/resident/mobile/InvoiceTable.jsx`
- `frontend/src/locales/th.js`
- `frontend/src/components/PullToRefresh.jsx` — เป็น shared component; เพิ่มเฉพาะการจัดการท่าสัมผัสที่ถูกยกเลิก

ไม่เปลี่ยน backend/API/schema/DB/permission/FIFO/การผูกยอดหรือยอดเงิน ไม่เพิ่มการคำนวณ OVERDUE; ลำดับ Admin ไม่เปลี่ยน

## ข้อค้นพบจากการทดสอบบนเบราว์เซอร์

ใช้ Chrome headless ตัวจริงผ่าน Playwright พร้อม viewport/touch emulation และคอมโพเนนต์ React จริงที่ import จาก repo บน localhost:5176. ข้อมูลทั้งหมดเป็นข้อมูลจำลอง ไม่มี API client/credentials/DB. ไม่ใช่ภาพ mockup และไม่ใช่การทดสอบบนโทรศัพท์จริง

รอบแรกหลังเติมสถานะ/วันที่ ผ่าน24 ไม่ผ่าน5:
- จอ360/390: จำนวนเงิน20,000.25 และ999,999.99ล้นเซลล์ (เซลล์75.33px แต่ข้อความ92.59/102.95px) — แก้ให้จำนวนเงินใช้3ส่วนของgrid พร้อม tabular-nums/nowrap; จัดหัวตารางให้ตรงกับขอบแถว
- ทั้ง3ขนาดจอ: ลากนอกตารางแล้วส่ง touchcancel จากนั้นแตะ/ลากตาราง ทำให้ refresh countเพิ่มจาก1→2โดยไม่ได้ตั้งใจ — พบว่า PullToRefresh ไม่มี onTouchCancel. Guard `!pulling` อย่างเดียวจึงไม่ครอบคลุมท่าที่ถูกยกเลิก; แก้ล้าง pulling/pullDistance/พิกัดเมื่อcancel

ปัญหาเตรียม harness แรกสุด: esbuild ใช้ JSX runtime แบบclassic ทำให้ PullToRefresh ไม่ render. แก้ **เฉพาะ harness** ให้ใช้ automatic JSX runtime ตรงกับ Vite ก่อนนับผลทดสอบ ไม่ใช่บั๊กโปรแกรม production

## ผลหลังแก้

**29 browser checks + 5 native input checks = 34 ผ่าน / 0 ไม่ผ่าน**

- viewport360,390,768: สถานะไทยครบ, null paid_at, เวลาข้ามวัน, รายการมาก24แถว, ข้ามปี, บิลพิเศษ, backfilled created_at, ID tie-break, frozen input props
- ตรวจขอบข้อความจริงของทุกเซลล์ ไม่พบจำนวนเงิน/วันที่/ป้ายสถานะล้นเซลล์; ยอดที่ตรวจ600 /20,000 /20,000.25 /999,999.99. เมื่อเลื่อนไปขวาบนจอแคบ คอลัมน์ฝั่งซ้ายออกนอก viewport ตามการเลื่อนแนวนอนปกติ
- วันที่และเวลาใน browser timezone UTC, Asia/Bangkok, Asia/Tokyo, America/New_York ให้ข้อความตรงกัน รวม due_date แบบdate-onlyและ timestamp18:30Z→01:30วันถัดไป
- max-height/overflow/page width/sticky headerผ่าน; wheelเลื่อนภายในตาราง, แสดงemptyและกลับมาrenderได้
- React touch events: ลากนอกตารางrefreshปกติ, ลากในตารางไม่refresh, cancelนอกตารางแล้วลากในตารางไม่refreshและไม่ทิ้งindicator
- Chrome native input via CDP: swipeแนวนอน/แนวตั้งจริงใน browserที่360และ390pxผ่านโดยไม่refresh; keyboard PageDownเลื่อนregionที่focusได้
- ไม่พบ page error หรือ external request ใน browser matrix; requestsถูกจำกัดlocalhost
- `npm run build` ผ่าน; `git diff --check` ผ่าน. มีwarningเดิม Browserslistเก่า/bundle>500KB; harness esbuildรายงานkeycycleซ้ำเดิมในหมวดinvoicesของlocale ซึ่งไม่ได้แก้ในรอบนี้

## หลักฐานและรันซ้ำ

แฟ้มส่วนตัวที่ไม่มีข้อมูลการเงินจริง: `C:\Users\sanch\moobaan-ui-checks\20260911-invoice-table`

- `fixture.jsx`, `server.cjs` — หน้า fixture ที่ใช้คอมโพเนนต์จริงและข้อมูลจำลอง
- `check.cjs`, `native-scroll.cjs` — browser acceptance scripts
- `initial-results.json` — 24ผ่าน/5ไม่ผ่านก่อนแก้คอลัมน์และtouchcancel
- `final-results.json` — 29ผ่าน/0ไม่ผ่าน
- `native-scroll-results.json` — 5ผ่าน
- `final-360-left.png`, `final-360-right.png`, `final-390-left.png`, `final-390-right.png`, `final-768-left.png`, `native-scroll-360.png`, `native-scroll-390.png`

Rebuild fixture จากfrontendโดยใช้ esbuildที่มีอยู่พร้อม `--jsx=automatic`, aliasreactไปfrontend/node_modules/react; สร้างCSSด้วยTailwind CLI/configจริง. จากแฟ้มหลักฐานรัน `node server.cjs`, `node check.cjs final`, `node native-scroll.cjs`. Scriptsใช้ bundled Playwright และsystemChrome; ไม่มีการเพิ่มdependency/package lockในrepo

## ขอบเขตความมั่นใจและขั้นถัดไป

ผ่านการตรวจคอมโพเนนต์จริงใน Chromeและมือถือจำลองแล้ว ยังไม่ใช่การตรวจSafari/iOS/Androidเครื่องจริง, LINE login หรือ E2E ทั้งdashboardกับAPI. ไม่มีการอ้างว่าshared PullToRefreshทุกหน้าถูกทดสอบครบ; normal/cancel behaviorของตัวจริงถูกตรวจในfixtureที่ใช้ร่วมกับตารางนี้

พร้อมส่ง Auditor/Owner รีวิว diffและภาพผลทดสอบก่อนพิจารณา commit/push. เอกสารปิดงานกระทบยอดที่ค้างในworking treeเป็นอีกชุดหนึ่ง ต้องแยกจากขอบเขตโปรแกรมUIนี้ในการรีวิว
