import { useState, useEffect, useCallback } from 'react';
import { expenseReconciliationAPI } from '../../api/client';
import ConfirmModal from '../../components/ConfirmModal';
import { SkeletonPage, SkeletonBlock } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';


export default function ExpenseReconciliation() {
  // State
  const [expenses, setExpenses] = useState([]);
  const [bankDebits, setBankDebits] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confirmRemove, setConfirmRemove] = useState({ open: false, allocId: null });
  const [success, setSuccess] = useState('');

  // Selection state
  const [selectedExpense, setSelectedExpense] = useState(null);
  const [selectedBankTxn, setSelectedBankTxn] = useState(null);
  const [matchAmount, setMatchAmount] = useState('');
  const [allocating, setAllocating] = useState(false);

  // Filter state
  const [expenseFilter, setExpenseFilter] = useState('PENDING');
  const [showUnallocatedOnly, setShowUnallocatedOnly] = useState(true);

  // View mode: 'match' or 'history'
  const [viewMode, setViewMode] = useState('match');

  // Fetch data
  const fetchExpenses = useCallback(async () => {
    try {
      const res = await expenseReconciliationAPI.listExpenses({ status: expenseFilter });
      setExpenses(res.data);
    } catch (err) {
      console.error('Failed to load expenses:', err);
    }
  }, [expenseFilter]);

  const fetchBankDebits = useCallback(async () => {
    try {
      const res = await expenseReconciliationAPI.listBankDebits({ unallocated_only: showUnallocatedOnly });
      setBankDebits(res.data);
    } catch (err) {
      console.error('Failed to load bank debits:', err);
    }
  }, [showUnallocatedOnly]);

  const fetchAllocations = useCallback(async () => {
    try {
      const params = {};
      if (selectedExpense) params.expense_id = selectedExpense.id;
      const res = await expenseReconciliationAPI.listAllocations(params);
      setAllocations(res.data);
    } catch (err) {
      console.error('Failed to load allocations:', err);
    }
  }, [selectedExpense]);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchExpenses(), fetchBankDebits()]);
    setLoading(false);
  }, [fetchExpenses, fetchBankDebits]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  useEffect(() => {
    if (selectedExpense) {
      fetchAllocations();
    } else {
      setAllocations([]);
    }
  }, [selectedExpense, fetchAllocations]);

  // When expense is selected, suggest the remaining amount
  useEffect(() => {
    if (selectedExpense && selectedBankTxn) {
      const expRemaining = selectedExpense.remaining || 0;
      const txnRemaining = selectedBankTxn.remaining || 0;
      const suggested = Math.min(expRemaining, txnRemaining);
      setMatchAmount(suggested > 0 ? suggested.toFixed(2) : '');
    }
  }, [selectedExpense, selectedBankTxn]);

  // Handle allocation
  const handleAllocate = async () => {
    if (!selectedExpense || !selectedBankTxn || !matchAmount) {
      setError('Please select an expense, a bank transaction, and enter an amount');
      return;
    }
    const amount = parseFloat(matchAmount);
    if (isNaN(amount) || amount <= 0) {
      setError('Amount must be greater than 0');
      return;
    }

    setAllocating(true);
    setError('');
    setSuccess('');

    try {
      const res = await expenseReconciliationAPI.allocate({
        expense_id: selectedExpense.id,
        bank_transaction_id: selectedBankTxn.id,
        matched_amount: amount,
      });
      setSuccess(res.data.message);
      // Refresh data
      await fetchAll();
      if (selectedExpense) {
        fetchAllocations();
      }
      // Clear bank txn selection (keep expense selected for further matching)
      setSelectedBankTxn(null);
      setMatchAmount('');
      // Update selected expense in list
      const updated = (await expenseReconciliationAPI.listExpenses({ status: expenseFilter })).data;
      setExpenses(updated);
      const updatedExp = updated.find(e => e.id === selectedExpense.id);
      if (updatedExp) setSelectedExpense(updatedExp);
    } catch (err) {
      setError(err.response?.data?.detail || 'Allocation failed');
    } finally {
      setAllocating(false);
    }
  };

  // Handle remove allocation
  const handleRemoveAllocation = async (allocId) => {
    setConfirmRemove({ open: false, allocId: null });
    setError('');
    setSuccess('');
    try {
      const res = await expenseReconciliationAPI.removeAllocation(allocId);
      setSuccess(res.data.message);
      await fetchAll();
      fetchAllocations();
      // Refresh selected expense
      const updated = (await expenseReconciliationAPI.listExpenses({ status: expenseFilter })).data;
      setExpenses(updated);
      const updatedExp = updated.find(e => e.id === selectedExpense?.id);
      if (updatedExp) setSelectedExpense(updatedExp);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to remove allocation');
    }
  };

  const formatMoney = (val) => {
    if (val == null) return '—';
    return `฿${Number(val).toLocaleString('en', { minimumFractionDigits: 2 })}`;
  };

  const formatDate = (d) => {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('th-TH', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">💳 Expense ↔ Bank Reconciliation</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('match')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${viewMode === 'match' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            Match
          </button>
          <button
            onClick={() => setViewMode('history')}
            className={`px-4 py-2 text-sm font-medium rounded-lg ${viewMode === 'history' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            History
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {success}
        </div>
      )}

      {loading ? (
        <SkeletonPage />
      ) : viewMode === 'match' ? (
        <>
          {/* Allocation Panel (shown when both selected) */}
          {selectedExpense && selectedBankTxn && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-3">{t('expenseRecon.createAllocation')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div>
                  <p className="text-sm text-gray-600">รายจ่าย #{selectedExpense.id}</p>
                  <p className="font-medium">{selectedExpense.description}</p>
                  <p className="text-sm">
                    Amount: {formatMoney(selectedExpense.amount)} | 
                    Remaining: <span className="text-blue-600 font-semibold">{formatMoney(selectedExpense.remaining)}</span>
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">รายการธนาคาร</p>
                  <p className="font-medium text-sm">{selectedBankTxn.description?.substring(0, 50)}</p>
                  <p className="text-sm">
                    Debit: {formatMoney(selectedBankTxn.debit)} | 
                    Remaining: <span className="text-blue-600 font-semibold">{formatMoney(selectedBankTxn.remaining)}</span>
                  </p>
                </div>
                <div className="flex items-end gap-2">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">จำนวนเงิน (฿)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={matchAmount}
                      onChange={(e) => setMatchAmount(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <button
                    onClick={handleAllocate}
                    disabled={allocating}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
                  >
                    {allocating ? 'Saving...' : '✓ Allocate'}
                  </button>
                  <button
                    onClick={() => { setSelectedBankTxn(null); setMatchAmount(''); }}
                    className="px-3 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Two-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* LEFT: Expenses */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                <h2 className="font-semibold text-gray-800">📋 Expenses</h2>
                <select
                  value={expenseFilter}
                  onChange={(e) => { setExpenseFilter(e.target.value); setSelectedExpense(null); }}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="PENDING">รอดำเนินการ</option>
                  <option value="PAID">ชำระแล้ว</option>
                  <option value="ALL">ทั้งหมด</option>
                </select>
              </div>
              <div className="divide-y max-h-[500px] overflow-y-auto">
                {expenses.length === 0 ? (
                  <p className="text-center py-8 text-gray-400">ไม่พบรายจ่าย</p>
                ) : expenses.map((exp) => (
                  <div
                    key={exp.id}
                    onClick={() => setSelectedExpense(selectedExpense?.id === exp.id ? null : exp)}
                    className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedExpense?.id === exp.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 truncate">{exp.description}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            exp.status === 'PAID' ? 'bg-green-100 text-green-700' :
                            exp.status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-500'
                          }`}>
                            {exp.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-500 mt-0.5">
                          {exp.vendor_name || 'No vendor'} • {formatDate(exp.expense_date)}
                        </p>
                        {exp.allocation_count > 0 && (
                          <p className="text-xs text-blue-600 mt-1">
                            {exp.allocation_count} allocation(s) • Matched: {formatMoney(exp.total_allocated)}
                          </p>
                        )}
                      </div>
                      <div className="text-right ml-3 shrink-0">
                        <p className="font-semibold text-gray-900">{formatMoney(exp.amount)}</p>
                        {exp.remaining > 0 && exp.remaining < exp.amount && (
                          <p className="text-xs text-orange-600">คงเหลือ: {formatMoney(exp.remaining)}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* RIGHT: Bank Debits */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
                <h2 className="font-semibold text-gray-800">🏦 Bank Debits</h2>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showUnallocatedOnly}
                    onChange={(e) => setShowUnallocatedOnly(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  Unallocated only
                </label>
              </div>
              <div className="divide-y max-h-[500px] overflow-y-auto">
                {bankDebits.length === 0 ? (
                  <p className="text-center py-8 text-gray-400">ไม่พบรายการเดบิตธนาคาร</p>
                ) : bankDebits.map((txn) => (
                  <div
                    key={txn.id}
                    onClick={() => {
                      if (!selectedExpense) {
                        setError('Please select an expense first');
                        return;
                      }
                      setSelectedBankTxn(selectedBankTxn?.id === txn.id ? null : txn);
                    }}
                    className={`px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedBankTxn?.id === txn.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    } ${!selectedExpense ? 'opacity-60' : ''}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 text-sm truncate">{txn.description}</p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {formatDate(txn.effective_at)} {txn.channel ? `• ${txn.channel}` : ''}
                        </p>
                        {txn.allocation_count > 0 && (
                          <p className="text-xs text-blue-600 mt-1">
                            {txn.allocation_count} allocation(s) • Used: {formatMoney(txn.total_allocated)}
                          </p>
                        )}
                      </div>
                      <div className="text-right ml-3 shrink-0">
                        <p className="font-semibold text-red-600">{formatMoney(txn.debit)}</p>
                        {txn.remaining > 0 && txn.remaining < txn.debit && (
                          <p className="text-xs text-orange-600">คงเหลือ: {formatMoney(txn.remaining)}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Selected Expense Allocations */}
          {selectedExpense && allocations.length > 0 && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-4 py-3 border-b bg-gray-50">
                <h3 className="font-semibold text-gray-800">
                  🔗 Allocations for Expense #{selectedExpense.id}: {selectedExpense.description}
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">รายการธนาคาร</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">วันที่</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">จับคู่แล้ว</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">สร้างเมื่อ</th>
                      <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">จัดการ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {allocations.map((a) => (
                      <tr key={a.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 text-sm text-gray-900">{a.bank_description?.substring(0, 40) || a.bank_transaction_id?.substring(0, 8)}</td>
                        <td className="px-4 py-2 text-sm text-gray-600">{formatDate(a.bank_effective_at)}</td>
                        <td className="px-4 py-2 text-sm text-right font-semibold text-blue-700">{formatMoney(a.matched_amount)}</td>
                        <td className="px-4 py-2 text-sm text-right text-gray-500">{formatDate(a.created_at)}</td>
                        <td className="px-4 py-2 text-center">
                          <button
                            onClick={(e) => { e.stopPropagation(); setConfirmRemove({ open: true, allocId: a.id }); }}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      ) : (
        /* History view — all allocations */
        <AllocationHistory />
      )}
      <ConfirmModal
        open={confirmRemove.open}
        title="ยกเลิกการจัดสรร"
        message="ต้องการยกเลิกการจัดสรรนี้ใช่หรือไม่?"
        variant="danger"
        confirmText="Remove"
        onConfirm={() => handleRemoveAllocation(confirmRemove.allocId)}
        onCancel={() => setConfirmRemove({ open: false, allocId: null })}
      />
    </div>
  );
}

// ===== History Sub-component =====
function AllocationHistory() {
  const [allocations, setAllocations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await expenseReconciliationAPI.listAllocations({});
        setAllocations(res.data);
      } catch (err) {
        console.error('Failed to load allocations:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const formatMoney = (val) => {
    if (val == null) return '—';
    return `฿${Number(val).toLocaleString('en', { minimumFractionDigits: 2 })}`;
  };

  const formatDate = (d) => {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('th-TH', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  if (loading) return <SkeletonPage />;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-4 py-3 border-b bg-gray-50">
        <h2 className="font-semibold text-gray-800">📜 All Allocations ({allocations.length})</h2>
      </div>
      {allocations.length === 0 ? (
        <p className="text-center py-8 text-gray-400">{t('expenseRecon.noAllocations')}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('expenseRecon.expense')}</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">ผู้รับเงิน</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">รายละเอียดธนาคาร</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">วันที่ธนาคาร</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">จับคู่แล้ว</th>
                <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">สถานะรายจ่าย</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">สร้างเมื่อ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {allocations.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm text-gray-900">#{a.expense_id} {a.expense_description?.substring(0, 30)}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{a.expense_vendor_name || '—'}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{a.bank_description?.substring(0, 35) || '—'}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{formatDate(a.bank_effective_at)}</td>
                  <td className="px-4 py-2 text-sm text-right font-semibold text-blue-700">{formatMoney(a.matched_amount)}</td>
                  <td className="px-4 py-2 text-center">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      a.expense_status === 'PAID' ? 'bg-green-100 text-green-700' :
                      a.expense_status === 'PENDING' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-500'
                    }`}>
                      {a.expense_status || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-right text-gray-500">{formatDate(a.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
    </AdminPageWrapper>
  );
}
