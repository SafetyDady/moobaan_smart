# Emoji Survey — Phase 3B Task 3.1

## Resident Mobile Pages

### MobileSubmitPayment.jsx
- `❌` error messages (setError) → AlertCircle or XCircle
- `✅` success messages → CheckCircle
- `⚠️` warning messages → AlertTriangle
- `✏️` edit header → Edit3/Pencil
- `💳` submit header → CreditCard
- `💡` hint text (3 places) → Lightbulb
- `📷` camera icon → Camera (already rendered as `�`)
- `⏳` submitting → Loader2

### PayinDetailModal.jsx
- `✕` close button → X
- `⚠️` reject reason → AlertTriangle
- `📝` admin note → FileText
- `✏️` edit button → Edit3
- `🗑️` delete button → Trash2
- `✓` confirmed → Check
- `📝` can edit → FileText

### PaymentHistory.jsx
- `📸` empty payin state → Camera
- `📄` empty invoice state → FileText

### Profile.jsx
- `✅` success toast → CheckCircle
- `❌` error toast → XCircle
- `🟢` active status → Circle (green)

### VillageDashboard.jsx
- `📊` empty chart → BarChart3
- Category icons (ELECTRICITY ⚡, WATER 💧, SECURITY 🛡️, etc.) → Lucide equivalents
- `📌` default category → Pin

## Admin Pages (high volume)

### ExpensesV2.jsx
- `➕` add → Plus
- `✏️` edit → Edit3
- `✅` mark paid → CheckCircle
- `❌` cancel → XCircle
- `📎` attachments → Paperclip
- `⏳` uploading → Loader2
- `📄` upload invoice → FileText
- `💡` hint → Lightbulb
- `👁️` view → Eye
- `🗑️` delete → Trash2

### Houses.jsx
- `🏠` house icon → Home
- `👤` add resident → UserPlus
- `🔄` refresh → RefreshCw
- `✏️` edit → Edit3
- `📄` PDF → FileText
- `📊` Excel → FileSpreadsheet
- `💾` save → Save
- `✕` close → X

### Members.jsx
- `✅` success → CheckCircle
- `❌` failed → XCircle
- `⚠️` warning → AlertTriangle
- `👥` members → Users
- `🏠` house → Home
- `📱` phone → Phone
- `🔑` reset password → Key

### PayIns.jsx
- `💳` icon → CreditCard
- `🔍` debug → Search

### UserManagement.jsx
- `👤` staff → User
- `🏠` residents → Home
- `🔑` reset → Key
- `🚫` deactivate → Ban
- `✅` activate → CheckCircle
- `👥` empty → Users

### Vendors.jsx
- `🏢` title → Building2
- `✅` success → CheckCircle

### InvoiceAgingReport.jsx
- `🎉` no overdue → PartyPopper (not in Lucide, use CheckCircle2)

### Invoices.jsx
- `📄` empty → FileText

### UnidentifiedReceipts.jsx
- `✅` all matched → CheckCircle

## Shared Components
- EmptyState.jsx: `📋` default icon prop → ClipboardList
- CreditNoteModal.jsx: `🎁` → Gift
