import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Users, Coins, Landmark, RefreshCw } from 'lucide-react';
import MobileLayout from './MobileLayout';
import { api } from '../../../api/client';

export default function VillageDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/dashboard/village-summary');
      setData(response.data);
    } catch (err) {
      console.error('Failed to load village summary:', err);
      setError('ไม่สามารถโหลดข้อมูลได้');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        </div>
      </MobileLayout>
    );
  }
  
  if (error) {
    return (
      <MobileLayout>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <div className="text-red-400">{error}</div>
          <button onClick={loadData} className="px-4 py-2 bg-primary-500 text-white rounded-lg">ลองอีกครั้ง</button>
        </div>
      </MobileLayout>
    );
  }
  
  if (!data) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">ไม่มีข้อมูล</div>
        </div>
      </MobileLayout>
    );
  }

  // Thai date formatting
  const thaiMonths = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  const thaiMonthsFull = ['', 'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'];
  
  // Header date
  const now = new Date();
  const headerDate = `${now.getDate()} ${thaiMonthsFull[now.getMonth() + 1] || ''} ${now.getFullYear() + 543}`;

  // Time ago for balance
  const getTimeAgo = () => {
    if (!data.balance_as_of) return 'ยังไม่มีข้อมูล';
    const diff = Math.floor((Date.now() - new Date(data.balance_as_of).getTime()) / 60000);
    if (diff < 1) return 'อัปเดตเมื่อสักครู่';
    if (diff < 60) return `อัปเดตเมื่อ ${diff} นาทีที่แล้ว`;
    if (diff < 1440) return `อัปเดตเมื่อ ${Math.floor(diff / 60)} ชม.ที่แล้ว`;
    return `อัปเดตเมื่อ ${Math.floor(diff / 1440)} วันที่แล้ว`;
  };

  // Format compact amounts
  const fmtK = (v) => v >= 1000 ? `฿${(v / 1000).toFixed(1)}k` : `฿${v.toLocaleString('th-TH')}`;
  const fmtAmount = (v) => `฿${(v || 0).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  // Chart: vertical stacked bars
  const months = data.monthly_income || [];
  const chartMax = Math.max(...months.map(m => (m.income || 0) + (m.expense || 0)), 1);
  // Round up to nearest nice step
  const niceMax = (() => {
    const raw = chartMax;
    if (raw <= 0) return 100000;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    return Math.ceil(raw / (mag / 2)) * (mag / 2);
  })();
  const ySteps = 5;
  const yLabels = Array.from({ length: ySteps + 1 }, (_, i) => (niceMax / ySteps) * (ySteps - i));

  return (
    <MobileLayout>
      <div className="p-4 space-y-4">
        {/* ── Header Card ── */}
        <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-700 rounded-2xl p-5 border border-gray-600/50 shadow-lg">
          {/* Title row */}
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-gray-300 font-medium">ภาพรวมหมู่บ้าน (Village Dashboard)</p>
            <button onClick={loadData} className="text-gray-400 hover:text-white transition-colors" title="รีเฟรช">
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          <p className="text-xl font-bold text-white mb-4">{headerDate}</p>

          {/* Balance */}
          <p className="text-sm text-gray-400 mb-1">ยอดเงินในบัญชีล่าสุด</p>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-3xl font-bold text-emerald-400">
              ฿{(data.total_balance || 0).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <Landmark size={24} className="text-emerald-500/70" />
          </div>
          <p className="text-xs text-gray-500">{getTimeAgo()}</p>
        </div>

        {/* ── Income / Expense Cards ── */}
        <div className="grid grid-cols-2 gap-3">
          {/* Income */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <ArrowUp size={16} className="text-emerald-400" />
              </div>
              <span className="text-sm text-gray-400">รายรับ</span>
            </div>
            <p className="text-xl font-bold text-white mb-1">
              {fmtAmount(data.total_income)}
            </p>
            <p className="text-xs text-gray-500">จากเดือนที่แล้ว</p>
          </div>

          {/* Expense */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center">
                <ArrowDown size={16} className="text-orange-400" />
              </div>
              <span className="text-sm text-gray-400">รายจ่าย</span>
            </div>
            <p className="text-xl font-bold text-white mb-1">
              {fmtAmount(data.total_expense)}
            </p>
            <p className="text-xs text-gray-500">จากเดือนที่แล้ว</p>
          </div>
        </div>

        {/* ── Debtor / Debt Cards ── */}
        <div className="grid grid-cols-2 gap-3">
          {/* Debtor Count */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                <Users size={16} className="text-blue-400" />
              </div>
              <span className="text-sm text-gray-400">ลูกหนี้</span>
            </div>
            <p className="text-xl font-bold text-white">
              {data.debtor_count} <span className="text-sm font-normal text-gray-400">ครัวเรือน</span>
            </p>
          </div>

          {/* Total Debt */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
                <Coins size={16} className="text-red-400" />
              </div>
              <span className="text-sm text-gray-400">มูลค่าหนี้</span>
            </div>
            <p className="text-xl font-bold text-white">
              ฿{(data.total_debt || 0).toLocaleString('th-TH', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        {/* ── Monthly Chart — Vertical Stacked Bars ── */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <h3 className="text-base font-semibold text-white mb-3">ภาพรวมรายเดือน <span className="text-xs font-normal text-gray-500">จาก Statement</span></h3>

          {months.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <div className="text-3xl mb-2">📊</div>
              <div className="text-sm">ยังไม่มีข้อมูล Statement</div>
            </div>
          ) : (
            <div>
              {/* Chart area */}
              <div className="flex">
                {/* Y-axis labels */}
                <div className="flex flex-col justify-between pr-1 text-right" style={{ height: 150, minWidth: 40 }}>
                  {yLabels.map((v, i) => (
                    <span key={i} className="text-[10px] text-gray-500 leading-none">
                      ฿{v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}
                    </span>
                  ))}
                </div>
                
                {/* Bars */}
                <div className="flex-1 relative border-l border-b border-gray-700" style={{ height: 150 }}>
                  {/* Grid lines */}
                  {yLabels.map((_, i) => (
                    <div
                      key={i}
                      className="absolute w-full border-t border-gray-700/50"
                      style={{ top: `${(i / ySteps) * 100}%` }}
                    />
                  ))}

                  {/* Bar groups */}
                  <div className="flex items-end justify-around h-full px-0.5 relative z-10">
                    {months.map((month) => {
                      const inc = month.income || 0;
                      const exp = month.expense || 0;
                      const total = inc + exp;
                      const barPct = niceMax > 0 ? (total / niceMax) * 100 : 0;
                      // Use pixel-based heights for reliability
                      const barPx = Math.max((barPct / 100) * 150, total > 0 ? 4 : 0);
                      const incPx = total > 0 ? (inc / total) * barPx : 0;
                      const expPx = total > 0 ? (exp / total) * barPx : 0;

                      return (
                        <div key={month.period} className="flex flex-col items-center justify-end h-full" style={{ width: `${100 / months.length}%` }}>
                          {/* Amount label above bar */}
                          <div className="text-[8px] text-center leading-tight mb-0.5 whitespace-nowrap">
                            <span className="text-emerald-400">{fmtK(inc)}</span>
                            <br />
                            <span className="text-orange-400">({fmtK(exp)})</span>
                          </div>
                          {/* Stacked bar — income on bottom (green), expense on top (orange) */}
                          <div className="w-6 sm:w-8 flex flex-col rounded-t-sm overflow-hidden">
                            <div className="bg-orange-500" style={{ height: expPx }} />
                            <div className="bg-emerald-500" style={{ height: incPx }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* X-axis month labels */}
              <div className="flex pl-8">
                {months.map((month) => (
                  <div key={month.period} className="text-center text-[10px] text-gray-400 mt-1" style={{ width: `${100 / months.length}%` }}>
                    {month.label}
                  </div>
                ))}
              </div>

              {/* Legend */}
              <div className="flex items-center justify-center gap-6 mt-3 text-xs">
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-emerald-500 inline-block"></span> รายรับ (Income)</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-orange-500 inline-block"></span> รายจ่าย (Expense)</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </MobileLayout>
  );
}
