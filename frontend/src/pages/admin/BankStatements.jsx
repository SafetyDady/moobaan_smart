import { useState, useEffect } from 'react';
import { bankStatementsAPI, bankAccountsAPI } from '../../api/client';
import ConfirmModal from '../../components/ConfirmModal';
import { useAuth } from '../../contexts/AuthContext';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';


const BankStatements = () => {
  const { user } = useAuth();
  const [bankAccounts, setBankAccounts] = useState([]);
  const [batches, setBatches] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [confirmImport, setConfirmImport] = useState(false);
  const [confirmDeleteBatch, setConfirmDeleteBatch] = useState({ open: false, batchId: null, filename: '' });
  const [success, setSuccess] = useState(null);
  
  // Transactions view state
  const [selectedBatchId, setSelectedBatchId] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [transactionsError, setTransactionsError] = useState(null);
  const [batchInfo, setBatchInfo] = useState(null);
  
  // Pagination for transactions
  const { sortConfig: txnSortConfig, requestSort: txnRequestSort, sortedData: sortedTransactions } = useSort(transactions);
  const pagedTransactions = usePagination(sortedTransactions);

  // New bank account form
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [newAccount, setNewAccount] = useState({
    bank_code: '',
    account_no_masked: '',
    account_type: 'CASHFLOW',
  });

  useEffect(() => {
    loadBankAccounts();
    loadBatches();
  }, []);

  const loadBankAccounts = async () => {
    try {
      const response = await bankAccountsAPI.list();
      // Robust normalization: handle {items: []}, [...], or {data: {items: []}}
      const raw = response.data;
      const accountsArray = Array.isArray(raw) 
        ? raw 
        : (raw?.items ?? raw?.data?.items ?? []);
      setBankAccounts(accountsArray);
      if (accountsArray.length > 0 && !selectedAccount) {
        setSelectedAccount(accountsArray[0].id);
      }
    } catch (err) {
      console.error('Failed to load bank accounts:', err);
      setBankAccounts([]); // Ensure array on error
    }
  };

  const loadBatches = async () => {
    try {
      const response = await bankStatementsAPI.listBatches();
      // Unwrap items from paginated response or use direct array, always ensure array
      const batchesData = response.data?.items ?? response.data ?? [];
      const batchesArray = Array.isArray(batchesData) ? batchesData : [];
      setBatches(batchesArray);
    } catch (err) {
      console.error('Failed to load batches:', err);
      setBatches([]); // Ensure array on error
    }
  };

  const handleAddAccount = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const response = await bankAccountsAPI.create(newAccount);
      const createdAccount = response.data;
      
      setSuccess('Bank account added successfully');
      setShowAddAccount(false);
      setNewAccount({ bank_code: '', account_no_masked: '', account_type: 'CASHFLOW' });
      
      // Refresh list and select newly created account
      await loadBankAccounts();
      if (createdAccount?.id) {
        setSelectedAccount(createdAccount.id);
      }
    } catch (err) {
      // Robust error message handling
      let errorMessage = t('bankStatements.addAccountFailed');
      
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        // Handle FastAPI validation errors (array format)
        if (Array.isArray(detail)) {
          errorMessage = detail.map(e => `• ${e.msg || e.message || e}`).join('\n');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (detail.message) {
          errorMessage = detail.message;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setPreview(null);
    setError(null);
    setSuccess(null);
  };

  const handlePreview = async () => {
    if (!file || !selectedAccount || !year || !month) {
      setError('Please select all required fields');
      return;
    }

    setLoading(true);
    setError(null);
    setPreview(null);

    try {
      const response = await bankStatementsAPI.uploadPreview(file, selectedAccount, year, month);

      setPreview(response.data);
      
      if (response.data.validation?.errors?.length > 0) {
        setError('Validation errors found. Please check below.');
      } else if (response.data.validation?.warnings?.length > 0) {
        setSuccess('Preview loaded with warnings');
      } else {
        setSuccess('Preview loaded successfully');
      }
    } catch (err) {
      // Enhanced error display
      const errorDetail = err.response?.data?.detail;
      const statusCode = err.response?.status;
      
      // Handle 409 Conflict (duplicate batch)
      if (statusCode === 409) {
        if (typeof errorDetail === 'object' && errorDetail !== null) {
          let errorMsg = errorDetail.message || t('bankStatements.batchDuplicate');
          errorMsg += '\n\n⚠️ ' + t('bankStatements.duplicateDetail') + ':';
          if (errorDetail.batch_id) errorMsg += '\n• Batch ID: ' + errorDetail.batch_id;
          if (errorDetail.batch_status) errorMsg += '\n• Status: ' + errorDetail.batch_status;
          if (errorDetail.uploaded_at) errorMsg += '\n• Uploaded: ' + errorDetail.uploaded_at;
          errorMsg += '\n\n💡 ' + t('bankStatements.duplicateHint');
          setError(errorMsg);
        } else {
          setError(t('bankStatements.batchDuplicateShort'));
        }
        return;
      }
      
      // Handle 422 Unprocessable Entity (missing file)
      if (statusCode === 422) {
        setError('CSV file is missing. Please select a file to upload.');
        return;
      }
      
      // Handle structured error with diagnostics
      if (typeof errorDetail === 'object' && errorDetail !== null) {
        let errorMsg = errorDetail.message || 'Failed to preview CSV';
        
        if (errorDetail.detected_columns && errorDetail.expected_columns) {
          errorMsg += '\n\n📋 Column Information:';
          errorMsg += '\n• Detected: ' + errorDetail.detected_columns.join(', ');
          errorMsg += '\n• Expected: ' + errorDetail.expected_columns.join(', ');
        }
        
        if (errorDetail.csv_date_range) {
          errorMsg += '\n\n📅 CSV Date Range: ' + errorDetail.csv_date_range.start + ' to ' + errorDetail.csv_date_range.end;
        }
        
        if (errorDetail.skip_reasons && Object.keys(errorDetail.skip_reasons).length > 0) {
          errorMsg += '\n\n⚠️ Parsing Issues:';
          const topReasons = Object.entries(errorDetail.skip_reasons)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 3);
          topReasons.forEach(([reason, count]) => {
            errorMsg += `\n• ${reason}: ${count} row(s)`;
          });
        }
        
        if (errorDetail.hint) {
          errorMsg += '\n\n💡 ' + errorDetail.hint;
        }
        
        setError(errorMsg);
      } else {
        // Simple string error
        setError(errorDetail || 'Failed to preview CSV');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!preview || preview.validation?.errors?.length > 0) {
      setError('Cannot import: validation errors exist');
      return;
    }

    setConfirmImport(false);
    setLoading(true);
    setError(null);

    try {
      const response = await bankStatementsAPI.confirmImport(file, selectedAccount, year, month);

      setSuccess(`Import successful! ${response.data.transaction_count} transactions imported.`);
      setPreview(null);
      setFile(null);
      await loadBatches();
      
      // Reset file input
      document.getElementById('file-input').value = '';
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'object' && detail.errors) {
        setError(`Import failed: ${detail.errors.join(', ')}`);
      } else {
        setError(detail || 'Failed to import bank statement');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (amount == null) return '-';
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB',
    }).format(amount);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('th-TH', {
      timeZone: 'Asia/Bangkok',
    });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('th-TH', {
      timeZone: 'Asia/Bangkok',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleViewTransactions = async (batchId) => {
    setSelectedBatchId(batchId);
    setTransactionsLoading(true);
    setTransactionsError(null);
    setTransactions([]);
    setBatchInfo(null);

    try {
      const response = await bankStatementsAPI.getBatchTransactions(batchId);
      const data = response.data;
      
      setTransactions(data.transactions || []);
      setBatchInfo(data.batch_info || null);
      setTransactionsError(null);
    } catch (err) {
      console.error('Failed to load transactions:', err);
      setTransactionsError(err.response?.data?.detail || 'Failed to load transactions');
      setTransactions([]);
    } finally {
      setTransactionsLoading(false);
    }
  };

  const handleCloseTransactions = () => {
    setSelectedBatchId(null);
    setTransactions([]);
    setBatchInfo(null);
    setTransactionsError(null);
  };

  const handleDeleteBatch = async (batchId, filename) => {
    setConfirmDeleteBatch({ open: false, batchId: null, filename: '' });
    try {
      setLoading(true);
      setError(null);
      const res = await bankStatementsAPI.deleteBatch(batchId);
      setSuccess(`${t('bankStatements.deleteBatchSuccess')} — ${res.data?.transactions_deleted || 0} ${t('bankStatements.transactionsDeleted')}`);
      // Close transactions view if this batch was open
      if (selectedBatchId === batchId) {
        handleCloseTransactions();
      }
      // Refresh batches list
      await loadBatches();
    } catch (err) {
      console.error('Failed to delete batch:', err);
      const detail = err.response?.data?.detail;
      const statusCode = err.response?.status;
      if (statusCode === 409) {
        setError(`${t('bankStatements.deleteFailed')}: ${detail}`);
      } else if (statusCode === 401) {
        setError(t('bankStatements.sessionExpired'));
      } else {
        setError(detail || 'Failed to delete batch');
      }
    } finally {
      setLoading(false);
    }
  };

  // Safety guard: ensure bankAccounts is always an array for rendering
  const safeAccounts = Array.isArray(bankAccounts) ? bankAccounts : (bankAccounts?.items ?? []);
  const safeBatches = Array.isArray(batches) ? batches : (batches?.items ?? []);

  return (
    <AdminPageWrapper>
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">{t('bankStatements.title')}</h1>
        <button
          onClick={() => setShowAddAccount(!showAddAccount)}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          {showAddAccount ? t('common.cancel') : t('bankStatements.addAccount')}
        </button>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <pre className="whitespace-pre-wrap font-sans text-sm">{error}</pre>
        </div>
      )}

      {/* Add Bank Account Form */}
      {showAddAccount && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{t('bankStatements.addNewAccount')}</h2>
          <form onSubmit={handleAddAccount} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">{t('bankStatements.bankCode')}</label>
              <input
                type="text"
                value={newAccount.bank_code}
                onChange={(e) => setNewAccount({...newAccount, bank_code: e.target.value})}
                className="w-full border rounded px-3 py-2"
                placeholder="e.g., KBANK, SCB"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('bankStatements.accountNumberLabel')}</label>
              <input
                type="text"
                value={newAccount.account_no_masked}
                onChange={(e) => setNewAccount({...newAccount, account_no_masked: e.target.value})}
                className="w-full border rounded px-3 py-2"
                placeholder="e.g., xxx-x-xxxxx-1234"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">{t('bankStatements.accountType')}</label>
              <select
                value={newAccount.account_type}
                onChange={(e) => setNewAccount({...newAccount, account_type: e.target.value})}
                className="w-full border rounded px-3 py-2"
              >
                <option value="CASHFLOW">{t('bankStatements.cashflow')}</option>
                <option value="SAVINGS">{t('bankStatements.savings')}</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:bg-gray-400"
            >
              Add Account
            </button>
          </form>
        </div>
      )}

      {/* Upload Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">{t('bankStatements.uploadCsv')}</h2>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-1">{t('vendors.bankAccount')}</label>
            <select
              value={selectedAccount}
              onChange={(e) => setSelectedAccount(e.target.value)}
              className="w-full border rounded px-3 py-2"
              disabled={safeAccounts.length === 0}
            >
              <option value="">
                {safeAccounts.length === 0 ? t('bankStatements.noAccounts') : t('bankStatements.selectAccount')}
              </option>
              {safeAccounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.bank_code} - {account.account_no_masked}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('bankStatements.yearLabel')}</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value))}
              className="w-full border rounded px-3 py-2"
              min="2020"
              max="2030"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">{t('bankStatements.monthLabel')}</label>
            <select
              value={month}
              onChange={(e) => setMonth(parseInt(e.target.value))}
              className="w-full border rounded px-3 py-2"
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>
                  {new Date(2000, m - 1).toLocaleDateString('th-TH', { month: 'long' })}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">CSV File</label>
            <input
              id="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>

        <button
          onClick={handlePreview}
          disabled={loading || !file || !selectedAccount}
          className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {loading ? '⏳ Processing...' : 'Preview CSV'}
        </button>
      </div>

      {/* Preview Section */}
      {preview && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{t('common.preview')}</h2>

          {/* Validation Messages */}
          {preview.validation?.errors?.length > 0 && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
              <h3 className="font-semibold text-red-800 mb-2">❌ Errors (import blocked):</h3>
              <ul className="list-disc list-inside text-red-700">
                {preview.validation.errors.map((err, idx) => (
                  <li key={idx}>{err}</li>
                ))}
              </ul>
            </div>
          )}

          {preview.validation?.warnings?.length > 0 && (
            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4">
              <h3 className="font-semibold text-yellow-800 mb-2">⚠️ Warnings:</h3>
              <ul className="list-disc list-inside text-yellow-700">
                {preview.validation.warnings.map((warn, idx) => (
                  <li key={idx}>{warn}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Summary */}
          <div className="grid grid-cols-4 gap-4 mb-4 text-sm">
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-gray-600">{t('bankStatements.transactions')}</div>
              <div className="text-xl font-bold">{preview.transaction_count}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-gray-600">{t('bankStatements.dateRange')}</div>
              <div className="font-semibold">
                {formatDate(preview.date_range_start)} - {formatDate(preview.date_range_end)}
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-gray-600">{t('bankStatements.openingBalance')}</div>
              <div className="font-semibold">{formatCurrency(preview.opening_balance)}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-gray-600">{t('bankStatements.closingBalance')}</div>
              <div className="font-semibold">{formatCurrency(preview.closing_balance)}</div>
            </div>
          </div>

          {/* Transaction Table */}
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.dateCol')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.descriptionCol')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.descriptionExtra')}</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.debit')}</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.credit')}</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.balance')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.channelCol')}</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {preview.transactions.map((txn, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-sm whitespace-nowrap">{formatDateTime(txn.effective_at)}</td>
                    <td className="px-4 py-2 text-sm">{txn.description}</td>
                    <td className="px-4 py-2 text-sm text-gray-600">{txn.details || '-'}</td>
                    <td className="px-4 py-2 text-sm text-right text-red-600">
                      {txn.debit ? formatCurrency(txn.debit) : '-'}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-green-600">
                      {txn.credit ? formatCurrency(txn.credit) : '-'}
                    </td>
                    <td className="px-4 py-2 text-sm text-right font-medium">
                      {formatCurrency(txn.balance)}
                    </td>
                    <td className="px-4 py-2 text-sm">{txn.channel || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Confirm Button */}
          {preview.validation?.errors?.length === 0 && (
            <button
              onClick={() => setConfirmImport(true)}
              disabled={loading}
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600 disabled:bg-gray-400"
            >
              {loading ? t('common.loading') : t('bankStatements.confirmImport')}
            </button>
          )}
        </div>
      )}

      {/* Existing Batches */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">{t('bankStatements.importedBatches')}</h2>
        
        {safeBatches.length === 0 ? (
          <p className="text-gray-500">{t('bankStatements.noImportedData')}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('common.date')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.account')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.period')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.file')}</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.transactions')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('common.status')}</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('common.actions')}</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {safeBatches.map((batch) => {
                  const account = safeAccounts.find(a => a.id === batch.bank_account_id);
                  return (
                    <tr key={batch.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm">{formatDate(batch.uploaded_at)}</td>
                      <td className="px-4 py-2 text-sm">
                        {account?.bank_code} - {account?.account_no_masked}
                      </td>
                      <td className="px-4 py-2 text-sm">
                        {batch.year}-{String(batch.month).padStart(2, '0')}
                      </td>
                      <td className="px-4 py-2 text-sm">{batch.original_filename}</td>
                      <td className="px-4 py-2 text-sm text-right">{batch.transaction_count}</td>
                      <td className="px-4 py-2 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${
                          batch.status === 'CONFIRMED' ? 'bg-green-100 text-green-800' :
                          batch.status === 'PARSED' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {batch.status}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm">
                        <button
                          onClick={() => handleViewTransactions(batch.id)}
                          className="text-blue-600 hover:text-blue-800 font-medium mr-3"
                        >
                        {t('common.view') || 'ดู'}
                      </button>
                        <button
                          onClick={() => setConfirmDeleteBatch({ open: true, batchId: batch.id, filename: batch.original_filename })}
                          className="text-red-500 hover:text-red-700 font-medium"
                        >
                        {t('common.delete')}
                      </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Transactions View Section */}
      {selectedBatchId && (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold">{t('bankStatements.batchTransactions')}</h2>
              {batchInfo && (
                <p className="text-sm text-gray-600 mt-1">
                  {batchInfo.filename} • {batchInfo.year}-{String(batchInfo.month).padStart(2, '0')}
                  {batchInfo.date_range_start && batchInfo.date_range_end && (
                    <> • {formatDate(batchInfo.date_range_start)} - {formatDate(batchInfo.date_range_end)}</>
                  )}
                </p>
              )}
            </div>
            <button
              onClick={handleCloseTransactions}
              className="text-gray-600 hover:text-gray-800 font-medium"
            >
              ✕ Close
            </button>
          </div>

          {transactionsLoading && (
            <div className="text-center py-8">
              <p className="text-gray-600">{t('common.loading')}</p>
            </div>
          )}

          {transactionsError && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
              <p className="text-red-700">{transactionsError}</p>
            </div>
          )}

          {!transactionsLoading && !transactionsError && transactions.length === 0 && (
            <p className="text-gray-500 text-center py-8">{t('bankStatements.noTransactions')}</p>
          )}

          {!transactionsLoading && !transactionsError && transactions.length > 0 && (
            <div>
              <p className="text-sm text-gray-600 mb-4">
                {t('common.total')}: {transactions.length} {t('bankStatements.transactions')}
              </p>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('common.date')}</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('common.description')}</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.additionalDetail')}</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.debit')}</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.credit')}</th>
                      <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">{t('bankStatements.balance')}</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{t('bankStatements.channel')}</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {pagedTransactions.currentItems.map((txn) => (
                      <tr key={txn.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 text-sm text-gray-900 font-medium whitespace-nowrap">
                          {formatDateTime(txn.effective_at)}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-800">
                          {txn.description}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          {txn.raw_row && txn.raw_row.length > 12 ? txn.raw_row[12] : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-right text-red-600">
                          {txn.debit ? formatCurrency(txn.debit) : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-right text-green-600">
                          {txn.credit ? formatCurrency(txn.credit) : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-right font-medium text-gray-900">
                          {txn.balance ? formatCurrency(txn.balance) : '-'}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-600">
                          {txn.channel || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {transactions.length > 0 && <Pagination {...pagedTransactions} />}
            </div>
          )}
        </div>
      )}
      <ConfirmModal
        open={confirmImport}
        title={t('bankStatements.confirmImportTitle')}
        message={t('bankStatements.confirmImportMsg')}
        variant="info"
        confirmText={t('bankStatements.importBtn')}
        onConfirm={handleConfirmImport}
        onCancel={() => setConfirmImport(false)}
      />
      <ConfirmModal
        open={confirmDeleteBatch.open}
        title={t('bankStatements.deleteBatchTitle')}
        message={`${t('bankStatements.deleteBatchMsg')} "${confirmDeleteBatch.filename}"?`}
        variant="danger"
        confirmText={t('common.delete')}
        onConfirm={() => handleDeleteBatch(confirmDeleteBatch.batchId, confirmDeleteBatch.filename)}
        onCancel={() => setConfirmDeleteBatch({ open: false, batchId: null, filename: '' })}
      />
    </div>
    </AdminPageWrapper>
  );
};

export default BankStatements;
