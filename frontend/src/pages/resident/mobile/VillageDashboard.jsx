import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Users, Coins, Landmark, RefreshCw, Zap, Droplets, Shield, Sparkles, Wrench, ClipboardList, Home, Package, Pin, BarChart3 } from 'lucide-react';
import MobileLayout from './MobileLayout';
import { api } from '../../../api/client';
import PullToRefresh from '../../../components/PullToRefresh';
import { t } from '../../../hooks/useLocale';

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
      setError(t('villageDashboard.loadError'));
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
          <button onClick={loadData} className="px-4 py-2 bg-primary-500 text-white rounded-lg">{t('villageDashboard.retry')}</button>
        </div>
      </MobileLayout>
    );
  }
  
  if (!data) {
    return (
      <MobileLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">{t('villageDashboard.noData')}</div>
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
    if (!data.balance_as_of) return t('villageDashboard.noData');
    const diff = Math.floor((Date.now() - new Date(data.balance_as_of).getTime()) / 60000);
    if (diff < 1) return t('villageDashboard.updatedJustNow');
    if (diff < 60) return `${t('villageDashboard.updatedAgo')} ${diff} ${t('villageDashboard.minutesAgo')}`;
    if (diff < 1440) return `${t('villageDashboard.updatedAgo')} ${Math.floor(diff / 60)} ${t('villageDashboard.hoursAgo')}`;
    return `${t('villageDashboard.updatedAgo')} ${Math.floor(diff / 1440)} ${t('villageDashboard.daysAgo')}`;
  };

  // Format compact amounts
  const fmtK = (v) => v >= 1000 ? `฿${(v / 1000).toFixed(1)}k` : `฿${v.toLocaleString('th-TH')}`;
  const fmtAmount = (v) => `฿${(v || 0).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  // ── FIX 3: Chart — Grouped Bars (not stacked) ──
  const months = data.monthly_income || [];
  // For grouped bars, niceMax is based on the single largest value (income or expense), not their sum
  const chartMax = Math.max(...months.flatMap(m => [m.income || 0, m.expense || 0]), 1);
  const niceMax = (() => {
    const raw = chartMax;
    if (raw <= 0) return 100000;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    return Math.ceil(raw / (mag / 2)) * (mag / 2);
  })();
  const ySteps = 5;
  const yLabels = Array.from({ length: ySteps + 1 }, (_, i) => (niceMax / ySteps) * (ySteps - i));

  const handleRefresh = async () => {
    await loadData();
  };

  return (
    <MobileLayout>
      <PullToRefresh onRefresh={handleRefresh}>
      <div className="p-4 space-y-4">
        {/* ── Header Card ── */}
        <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-700 rounded-2xl p-5 border border-gray-600/50 shadow-lg">
          {/* Title row */}
          <div className="flex items-center justify-between mb-1">
            <p className="text-sm text-gray-300 font-medium">{t('villageDashboard.title')}</p>
            <button onClick={loadData} className="text-gray-400 hover:text-white transition-colors" title={t('villageDashboard.refresh')}>
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          <p className="text-xl font-bold text-white mb-4">{headerDate}</p>

          {/* Balance */}
          <p className="text-sm text-gray-400 mb-1">{t('villageDashboard.latestBalance')}</p>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-3xl font-bold text-emerald-400">
              ฿{(data.total_balance || 0).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
            <Landmark size={24} className="text-emerald-500/70" />
          </div>
          <p className="text-xs text-gray-500">{getTimeAgo()}</p>
        </div>

        {/* ── FIX 1: Income / Expense Cards — side by side with overflow protection ── */}
        <div className="grid grid-cols-2 gap-3">
          {/* Income */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
                <ArrowUp size={16} className="text-emerald-400" />
              </div>
              <span className="text-sm text-gray-400 truncate">{t('villageDashboard.income')}</span>
            </div>
            <p className="text-lg font-bold text-white mb-1 truncate">
              {fmtAmount(data.total_income)}
            </p>
            <p className="text-xs text-gray-500">{t('villageDashboard.fromLastMonth')}</p>
          </div>

          {/* Expense */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-orange-500/20 flex items-center justify-center shrink-0">
                <ArrowDown size={16} className="text-orange-400" />
              </div>
              <span className="text-sm text-gray-400 truncate">{t('villageDashboard.expense')}</span>
            </div>
            <p className="text-lg font-bold text-white mb-1 truncate">
              {fmtAmount(data.total_expense)}
            </p>
            <p className="text-xs text-gray-500">{t('villageDashboard.fromLastMonth')}</p>
          </div>
        </div>

        {/* ── FIX 2: Debtor / Debt Cards — side by side with overflow protection ── */}
        <div className="grid grid-cols-2 gap-3">
          {/* Debtor Count */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0">
                <Users size={16} className="text-blue-400" />
              </div>
              <span className="text-sm text-gray-400 truncate">{t('villageDashboard.debtors')}</span>
            </div>
            <p className="text-xl font-bold text-white">
              {data.debtor_count}
            </p>
            <p className="text-xs text-gray-500">{t('villageDashboard.households')}</p>
          </div>

          {/* Total Debt */}
          <div className="bg-gray-800 rounded-xl p-4 border border-gray-700 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                <Coins size={16} className="text-red-400" />
              </div>
              <span className="text-sm text-gray-400 truncate">{t('villageDashboard.totalDebt')}</span>
            </div>
            <p className="text-lg font-bold text-white truncate">
              ฿{(data.total_debt || 0).toLocaleString('th-TH', { maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs text-gray-500">&nbsp;</p>
          </div>
        </div>

        {/* ── FIX 3: Monthly Chart — Grouped Bars (2 bars side by side per month) ── */}
        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
          <h3 className="text-base font-semibold text-white mb-3">{t('villageDashboard.monthlyOverview')} <span className="text-xs font-normal text-gray-500">{t('villageDashboard.fromStatement')}</span></h3>

          {months.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <div className="mb-2"><BarChart3 size={32} className="text-gray-500 mx-auto" /></div>
              <div className="text-sm">{t('villageDashboard.noStatementData')}</div>
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

                  {/* Grouped bar groups — 2 separate bars per month */}
                  <div className="flex items-end justify-around h-full px-0.5 relative z-10">
                    {months.map((month) => {
                      const inc = month.income || 0;
                      const exp = month.expense || 0;
                      // Each bar is independently scaled against niceMax
                      const incPct = niceMax > 0 ? (inc / niceMax) * 100 : 0;
                      const expPct = niceMax > 0 ? (exp / niceMax) * 100 : 0;

                      return (
                        <div key={month.period} className="flex flex-col items-center justify-end h-full" style={{ width: `${100 / months.length}%` }}>
                          {/* Amount labels above bars */}
                          <div className="text-[8px] text-center leading-tight mb-0.5 whitespace-nowrap">
                            <span className="text-emerald-400">{fmtK(inc)}</span>
                            <br />
                            <span className="text-orange-400">{fmtK(exp)}</span>
                          </div>
                          {/* Grouped bars — income (green) and expense (orange) side by side */}
                          <div className="flex items-end gap-0.5" style={{ height: '80%' }}>
                            <div
                              className="w-3 sm:w-4 bg-emerald-500 rounded-t-sm"
                              style={{ height: `${incPct}%`, minHeight: inc > 0 ? 2 : 0 }}
                            />
                            <div
                              className="w-3 sm:w-4 bg-orange-500 rounded-t-sm"
                              style={{ height: `${expPct}%`, minHeight: exp > 0 ? 2 : 0 }}
                            />
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
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-emerald-500 inline-block"></span> {t('villageDashboard.income')}</span>
                <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-orange-500 inline-block"></span> {t('villageDashboard.expense')}</span>
              </div>
            </div>
          )}
        </div>

        {/* ── FIX 4: Expense by Category — exact proportional bars (no minimum width hack) ── */}
        {(data.expense_by_category || []).length > 0 && (() => {
          const cats = data.expense_by_category;
          const periods = data.expense_periods || [];
          // globalMax from the single highest monthly value across ALL categories
          const globalMax = Math.max(...cats.flatMap(c => c.monthly.map(m => m.total)), 1);

          // Semantic color + icon per category
          const catMeta = {
            'ELECTRICITY': { icon: <Zap size={16} />, label: t('villageDashboard.catElectricity'), bar: 'bg-amber-500',   text: 'text-amber-400'   },
            'WATER':       { icon: <Droplets size={16} />, label: t('villageDashboard.catWater'),       bar: 'bg-cyan-500',    text: 'text-cyan-400'    },
            'SECURITY':    { icon: <Shield size={16} />, label: t('villageDashboard.catSecurity'),    bar: 'bg-blue-500',    text: 'text-blue-400'    },
            'CLEANING':    { icon: <Sparkles size={16} />, label: t('villageDashboard.catCleaning'),   bar: 'bg-emerald-500', text: 'text-emerald-400' },
            'MAINTENANCE': { icon: <Wrench size={16} />, label: t('villageDashboard.catMaintenance'), bar: 'bg-orange-500',  text: 'text-orange-400'  },
            'ADMIN':       { icon: <ClipboardList size={16} />, label: t('villageDashboard.catAdmin'),      bar: 'bg-purple-500',  text: 'text-purple-400'  },
            'UTILITIES':   { icon: <Home size={16} />, label: t('villageDashboard.catUtilities'),  bar: 'bg-teal-500',    text: 'text-teal-400'    },
            'OTHER':       { icon: <Package size={16} />, label: t('villageDashboard.catOther'),      bar: 'bg-gray-500',    text: 'text-gray-400'    },
          };
          const defaultMeta = { icon: <Pin size={16} />, label: '', bar: 'bg-gray-500', text: 'text-gray-400' };
          const grandTotal = cats.reduce((s, c) => s + c.grand_total, 0);

          return (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="flex items-baseline justify-between mb-4">
                <h3 className="text-base font-semibold text-white">
                  {t('villageDashboard.expenseByCategory')} <span className="text-xs font-normal text-gray-500">{t('villageDashboard.last3Months')}</span>
                </h3>
              </div>

              {/* Period header */}
              {periods.length > 0 && (
                <div className="flex items-center gap-3 mb-3 ml-0">
                  {periods.map((p, i) => (
                    <span key={p.period} className="text-[10px] text-gray-500">
                      {p.label} {p.year_label}
                    </span>
                  ))}
                </div>
              )}

              <div className="space-y-4">
                {cats.map((cat) => {
                  const meta = catMeta[cat.category] || { ...defaultMeta, label: cat.category };

                  return (
                    <div key={cat.category}>
                      {/* Category header */}
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-base leading-none">{meta.icon}</span>
                          <span className="text-sm font-medium text-gray-200">{meta.label}</span>
                        </div>
                        <span className={`text-sm font-semibold ${meta.text}`}>
                          ฿{cat.grand_total.toLocaleString('th-TH', { maximumFractionDigits: 0 })}
                        </span>
                      </div>

                      {/* Monthly mini-bars — FIX: exact proportional width from globalMax, no minimum width hack */}
                      <div className="space-y-1 ml-7">
                        {cat.monthly.map((m, mi) => {
                          // barW = (value / globalMax) * 100
                          // Same value ALWAYS produces same width — guaranteed
                          const barW = globalMax > 0 ? (m.total / globalMax) * 100 : 0;
                          // Change vs previous month
                          const prev = mi > 0 ? cat.monthly[mi - 1].total : null;
                          let pctChange = null;
                          if (prev !== null) {
                            if (prev === 0 && m.total > 0) {
                              pctChange = 100; // went from 0 to something
                            } else if (prev > 0) {
                              pctChange = ((m.total - prev) / prev) * 100;
                            } else if (prev === 0 && m.total === 0) {
                              pctChange = null; // both zero, no change to show
                            }
                          }

                          return (
                            <div key={m.period} className="flex items-center gap-2">
                              <span className="text-[10px] text-gray-500 w-8 text-right shrink-0">{m.label}</span>
                              <div className="flex-1 h-4 bg-gray-700/40 rounded overflow-hidden">
                                <div
                                  className={`h-full ${meta.bar} rounded transition-all duration-500`}
                                  style={{ width: `${barW}%` }}
                                />
                              </div>
                              <span className="text-[10px] text-gray-300 w-14 text-right shrink-0">
                                ฿{m.total >= 1000 ? `${(m.total / 1000).toFixed(1)}k` : m.total.toLocaleString('th-TH')}
                              </span>
                              {/* Always render w-10 slot so flex-1 bar container is equal width on every row */}
                              <span className={`text-[9px] w-10 text-right shrink-0 ${
                                pctChange === null ? 'invisible' :
                                pctChange > 0 ? 'text-red-400' : pctChange < 0 ? 'text-emerald-400' : 'text-gray-500'
                              }`}>
                                {pctChange !== null
                                  ? `${pctChange > 0 ? '↑' : pctChange < 0 ? '↓' : '—'}${Math.abs(pctChange).toFixed(0)}%`
                                  : '\u00A0'}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Grand total footer */}
              <div className="mt-4 pt-3 border-t border-gray-700 flex items-center justify-between">
                <span className="text-xs text-gray-400">{t('villageDashboard.grandTotal3Months')}</span>
                <span className="text-sm font-bold text-white">฿{grandTotal.toLocaleString('th-TH', { maximumFractionDigits: 0 })}</span>
              </div>
            </div>
          );
        })()}
      </div>
      </PullToRefresh>
    </MobileLayout>
  );
}
