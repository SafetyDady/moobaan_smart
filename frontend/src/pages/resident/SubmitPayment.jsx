import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { payinsAPI } from '../../api/client';
import { useRole } from '../../contexts/RoleContext';

export default function SubmitPayment() {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentHouseId } = useRole();
  const editPayin = location.state?.editPayin;

  const [formData, setFormData] = useState({
    amount: editPayin?.amount || '',
    transfer_date: editPayin?.transfer_date || '',
    transfer_hour: editPayin?.transfer_hour || '',
    transfer_minute: editPayin?.transfer_minute || '',
    slip_image_url: editPayin?.slip_image_url || '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const submitData = {
        house_id: currentHouseId,
        amount: parseFloat(formData.amount),
        transfer_date: formData.transfer_date,
        transfer_hour: parseInt(formData.transfer_hour),
        transfer_minute: parseInt(formData.transfer_minute),
        slip_image_url: formData.slip_image_url || 'https://example.com/slips/mock.jpg',
      };

      if (editPayin) {
        await payinsAPI.update(editPayin.id, submitData);
        alert('Payment slip updated and resubmitted successfully');
      } else {
        await payinsAPI.create(submitData);
        alert('Payment slip submitted successfully');
      }
      
      navigate('/resident/dashboard');
    } catch (error) {
      console.error('Failed to submit:', error);
      alert(error.response?.data?.detail || 'Failed to submit payment slip');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          {editPayin ? 'Edit & Resubmit Payment' : 'Submit Payment Slip'}
        </h1>
        <p className="text-gray-400">
          House #{currentHouseId} - Upload your payment slip details
        </p>
        {editPayin && (
          <div className="mt-4 p-4 bg-yellow-900 bg-opacity-30 border border-yellow-600 rounded-lg">
            <p className="text-yellow-300 text-sm">
              <strong>Rejection Reason:</strong> {editPayin.reject_reason}
            </p>
          </div>
        )}
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit} className="card p-6 space-y-6">
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Amount (฿) *
            </label>
            <input
              type="number"
              required
              step="0.01"
              min="0"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="input w-full"
              placeholder="3000.00"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Transfer Date *
            </label>
            <input
              type="date"
              required
              value={formData.transfer_date}
              onChange={(e) => setFormData({ ...formData, transfer_date: e.target.value })}
              className="input w-full"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Transfer Hour (HH) *
              </label>
              <input
                type="number"
                required
                min="0"
                max="23"
                value={formData.transfer_hour}
                onChange={(e) => setFormData({ ...formData, transfer_hour: e.target.value })}
                className="input w-full"
                placeholder="14"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Transfer Minute (MM) *
              </label>
              <input
                type="number"
                required
                min="0"
                max="59"
                value={formData.transfer_minute}
                onChange={(e) => setFormData({ ...formData, transfer_minute: e.target.value })}
                className="input w-full"
                placeholder="30"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Payment Slip Image
            </label>
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center">
              <div className="text-4xl mb-2">📎</div>
              <p className="text-gray-400 text-sm mb-2">
                Upload payment slip image
              </p>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  // Mock file upload - in production, upload to S3 and get URL
                  const file = e.target.files[0];
                  if (file) {
                    setFormData({ 
                      ...formData, 
                      slip_image_url: `https://example.com/slips/${file.name}` 
                    });
                  }
                }}
                className="hidden"
                id="slip-upload"
              />
              <label htmlFor="slip-upload" className="btn-secondary cursor-pointer inline-block">
                Choose File
              </label>
              {formData.slip_image_url && (
                <p className="text-primary-400 text-sm mt-2">
                  ✓ File selected
                </p>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Note: File upload is mocked in Phase 1
            </p>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary flex-1"
            >
              {submitting ? 'Submitting...' : (editPayin ? 'Update & Resubmit' : 'Submit')}
            </button>
            <button
              type="button"
              onClick={() => navigate('/resident/dashboard')}
              className="btn-secondary flex-1"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
