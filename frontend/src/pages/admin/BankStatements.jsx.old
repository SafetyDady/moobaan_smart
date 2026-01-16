import { useState, useEffect } from 'react';
import { bankStatementsAPI } from '../../api/client';

export default function BankStatements() {
  const [statements, setStatements] = useState([]);
  const [selectedStatement, setSelectedStatement] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadStatements();
  }, []);

  const loadStatements = async () => {
    try {
      const response = await bankStatementsAPI.list();
      setStatements(response.data);
      if (response.data.length > 0 && !selectedStatement) {
        loadRows(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to load statements:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRows = async (statementId) => {
    try {
      const response = await bankStatementsAPI.getRows(statementId);
      setRows(response.data);
      setSelectedStatement(statementId);
    } catch (error) {
      console.error('Failed to load rows:', error);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    try {
      await bankStatementsAPI.upload(file);
      alert('Bank statement uploaded successfully');
      loadStatements();
    } catch (error) {
      console.error('Failed to upload:', error);
      alert('Failed to upload bank statement');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Bank Statements</h1>
        <p className="text-gray-400">Upload and match bank statements with pay-ins</p>
      </div>

      {/* Upload */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-4">
          <label className="btn-primary cursor-pointer">
            {uploading ? 'Uploading...' : '📤 Upload Statement (Excel)'}
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
          <p className="text-sm text-gray-400">
            Upload Excel or CSV file with transaction data
          </p>
        </div>
      </div>

      {/* Statements List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-4">
          <h3 className="font-bold text-white mb-4">Uploaded Statements</h3>
          <div className="space-y-2">
            {loading ? (
              <div className="text-gray-400">Loading...</div>
            ) : statements.length === 0 ? (
              <div className="text-gray-400 text-sm">No statements uploaded</div>
            ) : (
              statements.map((stmt) => (
                <button
                  key={stmt.id}
                  onClick={() => loadRows(stmt.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedStatement === stmt.id
                      ? 'bg-primary-600 text-white'
                      : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                  }`}
                >
                  <div className="font-medium text-sm">{stmt.filename}</div>
                  <div className="text-xs opacity-75 mt-1">
                    {stmt.total_rows} rows, {stmt.matched_rows} matched
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Statement Rows */}
        <div className="lg:col-span-2 card">
          <div className="p-4 border-b border-gray-700">
            <h3 className="font-bold text-white">Transaction Rows</h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Amount</th>
                  <th>Reference</th>
                  <th>Match Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr><td colSpan="5" className="text-center py-8 text-gray-400">Select a statement to view rows</td></tr>
                ) : (
                  rows.map((row) => (
                    <tr key={row.id}>
                      <td className="text-gray-300">{new Date(row.date).toLocaleDateString()}</td>
                      <td className="text-gray-300">{row.time}</td>
                      <td className="font-medium text-white">฿{row.amount.toLocaleString()}</td>
                      <td className="text-gray-300">{row.reference}</td>
                      <td>
                        {row.matched ? (
                          <span className="badge badge-success">Matched</span>
                        ) : (
                          <button className="text-yellow-400 hover:text-yellow-300 text-sm">
                            Match
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
