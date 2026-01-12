import { useState, useEffect } from 'react';
import { expensesAPI } from '../../api/client';

export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExpenses();
  }, []);

  const loadExpenses = async () => {
    try {
      const response = await expensesAPI.list();
      setExpenses(response.data);
    } catch (error) {
      console.error('Failed to load expenses:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'badge-gray',
      approved: 'badge-warning',
      paid: 'badge-success',
    };
    return badges[status] || 'badge-gray';
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Expenses Management</h1>
        <p className="text-gray-400">Track village expenses and approvals</p>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Amount</th>
                <th>Description</th>
                <th>Status</th>
                <th>Receipt</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan="6" className="text-center py-8">Loading...</td></tr>
              ) : expenses.length === 0 ? (
                <tr><td colSpan="6" className="text-center py-8 text-gray-400">No expenses found</td></tr>
              ) : (
                expenses.map((exp) => (
                  <tr key={exp.id}>
                    <td className="text-gray-300">{new Date(exp.date).toLocaleDateString()}</td>
                    <td className="text-gray-300">{exp.category}</td>
                    <td className="font-medium text-white">฿{exp.amount.toLocaleString()}</td>
                    <td className="text-gray-300">{exp.description}</td>
                    <td><span className={`badge ${getStatusBadge(exp.status)}`}>{exp.status}</span></td>
                    <td>
                      {exp.receipt_url ? (
                        <a href={exp.receipt_url} target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:text-primary-300">
                          View
                        </a>
                      ) : (
                        <span className="text-gray-500">-</span>
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
  );
}
