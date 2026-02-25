import { useState, useEffect } from 'react';
import { ClipboardList, Search } from 'lucide-react';
import { expensesAPI } from '../../api/client';
import { SkeletonTable } from '../../components/Skeleton';
import { t } from '../../hooks/useLocale';
import AdminPageWrapper from '../../components/AdminPageWrapper';
import Pagination, { usePagination } from '../../components/Pagination';
import SortableHeader, { useSort } from '../../components/SortableHeader';
import EmptyState from '../../components/EmptyState';


export default function Expenses() {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  const { sortConfig, requestSort, sortedData } = useSort(expenses);
  const paged = usePagination(sortedData);

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

  const getStatusLabel = (status) => {
    const labels = {
      draft: t('common.statusDraft') || 'ร่าง',
      approved: t('common.statusApproved') || 'อนุมัติ',
      paid: t('common.statusPaid') || 'ชำระแล้ว',
    };
    return labels[status] || status;
  };

  return (
    <AdminPageWrapper>
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
                <SortableHeader label={t('common.date')} sortKey="date" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.category')} sortKey="category" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.amount')} sortKey="amount" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.description')} sortKey="description" sortConfig={sortConfig} onSort={requestSort} />
                <SortableHeader label={t('common.status')} sortKey="status" sortConfig={sortConfig} onSort={requestSort} />
                <th>{t('expenses.receipt') || 'ใบเสร็จ'}</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <SkeletonTable rows={5} cols={6} />
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan="6">
                    <EmptyState
                      icon={<ClipboardList size={32} />}
                      message={t('expenses.noData') || t('common.noData')}
                      description={t('expenses.noDataDesc') || 'ยังไม่มีรายการค่าใช้จ่าย'}
                    />
                  </td>
                </tr>
              ) : paged.currentItems.length === 0 ? (
                <tr>
                  <td colSpan="6">
                    <EmptyState
                      icon={<Search size={32} />}
                      message={t('common.noResults') || 'ไม่พบข้อมูล'}
                    />
                  </td>
                </tr>
              ) : (
                paged.currentItems.map((exp) => (
                  <tr key={exp.id}>
                    <td className="text-gray-300">{new Date(exp.date).toLocaleDateString('th-TH')}</td>
                    <td className="text-gray-300">{exp.category}</td>
                    <td className="font-medium text-white">฿{exp.amount.toLocaleString('th-TH')}</td>
                    <td className="text-gray-300">{exp.description}</td>
                    <td><span className={`badge ${getStatusBadge(exp.status)}`}>{getStatusLabel(exp.status)}</span></td>
                    <td>
                      {exp.receipt_url ? (
                        <a href={exp.receipt_url} target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:text-primary-300">
                          {t('common.view') || 'ดู'}
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
        {!loading && expenses.length > 0 && <Pagination {...paged} />}
      </div>
    </div>
    </AdminPageWrapper>
  );
}
