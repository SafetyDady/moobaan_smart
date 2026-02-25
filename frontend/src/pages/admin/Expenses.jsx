import { useState, useEffect } from 'react';
import { expensesAPI } from '../../api/client';
import { SkeletonTable } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';

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
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{t('expenses.title')}</h1>
        <p className="text-gray-400">{t('expenses.subtitle')}</p>
      </div>

      <div className="card">
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>{t('common.date')}</th>
                <th>{t('common.category')}</th>
                <th>{t('common.amount')}</th>
                <th>{t('common.description')}</th>
                <th>{t('common.status')}</th>
                <th>ใบเสร็จ</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={6} />
              ) : expenses.length === 0 ? (
                <tr><td colSpan="6" className="text-center py-8 text-gray-400">{t('common.noData')}</td></tr>
              ) : (
                expenses.map((exp) => (
                  <tr key={exp.id}>
                    <td className="text-gray-300">{new Date(exp.date).toLocaleDateString('th-TH')}</td>
                    <td className="text-gray-300">{exp.category}</td>
                    <td className="font-medium text-white">฿{exp.amount.toLocaleString('th-TH')}</td>
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
