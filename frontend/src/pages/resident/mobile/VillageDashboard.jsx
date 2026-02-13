import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown, Users, DollarSign, RefreshCw } from 'lucide-react';
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
          <div className="text-gray-400">กำลังโหลด...</div>
        </div>
      </MobileLayout>
    );
  }
  
  if (error) {
    return (
      <MobileLayout>
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <div className="text-red-400">{error}</div>
          <button
            onClick={loadData}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg"
          >
            ลองอีกครั้ง
          </button>
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
  
  const maxMonthlyAmount = Math.max(...(data.monthly_income || []).map(m => Math.max(m.amount || 0, m.expense || 0)), 1);
  
  return (
    <MobileLayout>
      <div className="p-4 space-y-4">
        {/* Main Balance Card */}
        <div className="bg-gradient-to-br from-primary-500 via-primary-600 to-blue-600 rounded-xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm text-white/80">ยอดเงินในบัญชีล่าสุด</div>
            <button onClick={loadData} className="text-white/60 hover:text-white transition-colors" title="รีเฟรช">
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
          <div className="text-4xl font-bold text-white">
            ฿{(data.total_balance || 0).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-white/60 mt-2">
            {data.balance_as_of 
              ? `ณ วันที่ ${new Date(data.balance_as_of).toLocaleDateString('th-TH', { year: 'numeric', month: 'long', day: 'numeric' })}`
              : 'ยังไม่มีข้อมูล Statement'
            }
          </div>
        </div>
        
        {/* Income/Expense/Debtor Grid */}
        <div className="grid grid-cols-2 gap-3">
          {/* Income */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">รายรับเดือนนี้</span>
              <ArrowUp size={20} className="text-green-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              ฿{data.total_income.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </div>
            {data.monthly_income.length > 1 && (
              <div className="text-xs text-green-400 mt-1">
                {data.monthly_income[0].amount > data.monthly_income[1].amount ? '↑' : '↓'} 
                {' '}
                {Math.abs(
                  ((data.monthly_income[0].amount - data.monthly_income[1].amount) / data.monthly_income[1].amount * 100) || 0
                ).toFixed(0)}%
              </div>
            )}
          </div>
          
          {/* Expense */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">รายจ่ายเดือนนี้</span>
              <ArrowDown size={20} className="text-red-400" />
            </div>
            <div className="text-2xl font-bold text-white">
              ฿{data.total_expense.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </div>
            {data.monthly_income?.length > 1 && (() => {
              const curr = data.monthly_income[0]?.expense || 0;
              const prev = data.monthly_income[1]?.expense || 0;
              if (prev === 0) return null;
              const pct = Math.abs(((curr - prev) / prev * 100)).toFixed(0);
              return (
                <div className={`text-xs mt-1 ${curr > prev ? 'text-red-400' : 'text-green-400'}`}>
                  {curr > prev ? '↑' : '↓'} {pct}%
                </div>
              );
            })()}
          </div>
          
          {/* Debtor Count */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">ลูกหนี้</span>
              <Users size={20} className="text-orange-400" />
            </div>
            <div className="text-2xl font-bold text-orange-400">
              {data.debtor_count} ราย
            </div>
            <div className="text-xs text-gray-500 mt-1">ยังไม่ชำระ</div>
          </div>
          
          {/* Total Debt */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">มูลค่าหนี้</span>
              <DollarSign size={20} className="text-red-400" />
            </div>
            <div className="text-2xl font-bold text-red-400">
              ฿{data.total_debt.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </div>
            <div className="text-xs text-gray-500 mt-1">ค้างชำระ</div>
          </div>
        </div>
        
        {/* Monthly Income/Expense Chart */}
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-300 mb-3">สถิติรายเดือน</h3>
          <div className="flex items-center gap-4 mb-3 text-xs">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-green-500 inline-block"></span> รายรับ</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-sm bg-red-500 inline-block"></span> รายจ่าย</span>
          </div>
          <div className="space-y-3">
            {(data.monthly_income || []).map(month => (
              <div key={month.period} className="space-y-1">
                <span className="text-xs text-gray-400">{month.label}</span>
                {/* Income bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-700 rounded-full h-5 overflow-hidden">
                    <div 
                      className="bg-green-500 h-full rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                      style={{ width: `${Math.max((month.amount / maxMonthlyAmount) * 100, month.amount > 0 ? 8 : 0)}%` }}
                    >
                      {month.amount > 0 && (
                        <span className="text-[10px] font-medium text-white whitespace-nowrap">
                          ฿{month.amount.toLocaleString('th-TH', { maximumFractionDigits: 0 })}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                {/* Expense bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-700 rounded-full h-5 overflow-hidden">
                    <div 
                      className="bg-red-500 h-full rounded-full flex items-center justify-end pr-2 transition-all duration-500"
                      style={{ width: `${Math.max(((month.expense || 0) / maxMonthlyAmount) * 100, (month.expense || 0) > 0 ? 8 : 0)}%` }}
                    >
                      {(month.expense || 0) > 0 && (
                        <span className="text-[10px] font-medium text-white whitespace-nowrap">
                          ฿{(month.expense || 0).toLocaleString('th-TH', { maximumFractionDigits: 0 })}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Recent Activity Feed */}
        <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-medium text-gray-300">กิจกรรมล่าสุด</h3>
          </div>
          
          {data.recent_activities && data.recent_activities.length > 0 ? (
            <div className="divide-y divide-gray-700">
              {data.recent_activities.map((activity, index) => (
                <div key={index} className="p-3 flex items-start gap-3">
                  <div className="text-2xl">{activity.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white">{activity.description}</div>
                    <div className="text-xs text-gray-400 mt-1">{activity.timestamp}</div>
                  </div>
                  <div className={`text-sm font-semibold ${
                    activity.type === 'income' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {activity.type === 'income' ? '+' : '-'}฿{activity.amount.toLocaleString('th-TH', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-gray-500">
              <div className="text-3xl mb-2">📊</div>
              <div className="text-sm">ยังไม่มีกิจกรรม</div>
            </div>
          )}
        </div>
        
        {/* Info Footer */}
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <div className="text-blue-400 mt-0.5">ℹ️</div>
            <div className="flex-1">
              <div className="text-xs text-blue-300">
                ข้อมูลนี้แสดงภาพรวมการเงินของหมู่บ้านทั้งหมด โดยไม่เปิดเผยข้อมูลส่วนบุคคล
              </div>
            </div>
          </div>
        </div>
      </div>
    </MobileLayout>
  );
}
