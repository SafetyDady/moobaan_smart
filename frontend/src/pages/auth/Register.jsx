import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../api/client';

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    name: '',
    house_number: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/api/auth/register', {
        username: formData.username,
        password: formData.password,
        name: formData.name,
        house_number: formData.house_number || null,
      });

      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
        <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700 text-center">
          <div className="text-primary-400 text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-white mb-4">Registration Successful!</h2>
          <p className="text-gray-300 mb-6">
            ลงทะเบียนสำเร็จ! กรุณารอ Admin อนุมัติบัญชีของคุณ
            <br />
            Please wait for admin approval.
          </p>
          <p className="text-gray-400 text-sm">
            Redirecting to login page...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4 py-8">
      <div className="max-w-md w-full">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-400 mb-2">
            🏘️ Village Accounting
          </h1>
          <p className="text-gray-400">ระบบบัญชีหมู่บ้านจัดสรรค์</p>
        </div>

        {/* Register Card */}
        <div className="bg-gray-800 rounded-lg shadow-xl p-8 border border-gray-700">
          <h2 className="text-2xl font-bold text-white mb-6">สมัครสมาชิก / Register</h2>

          {error && (
            <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ชื่อผู้ใช้ / Username <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter username"
                required
              />
            </div>

            {/* Full Name */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ชื่อ-นามสกุล / Full Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter full name"
                required
              />
            </div>

            {/* House Number */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                บ้านเลขที่ / House Number (optional)
              </label>
              <input
                type="text"
                name="house_number"
                value={formData.house_number}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., A-101"
              />
              <p className="mt-1 text-xs text-gray-500">
                สำหรับลูกบ้าน / For residents only
              </p>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                รหัสผ่าน / Password <span className="text-red-400">*</span>
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Enter password"
                required
                minLength={6}
              />
              <p className="mt-1 text-xs text-gray-500">
                อย่างน้อย 6 ตัวอักษร / At least 6 characters
              </p>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ยืนยันรหัสผ่าน / Confirm Password <span className="text-red-400">*</span>
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Re-enter password"
                required
              />
            </div>

            {/* Register Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'กำลังสมัครสมาชิก...' : 'สมัครสมาชิก / Register'}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 border-t border-gray-700"></div>

          {/* Login Link */}
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-2">
              มีบัญชีอยู่แล้ว? / Already have an account?
            </p>
            <Link
              to="/login"
              className="text-primary-400 hover:text-primary-300 font-medium"
            >
              เข้าสู่ระบบ / Login
            </Link>
          </div>

          {/* Note */}
          <div className="mt-6 p-4 bg-blue-900/30 rounded-lg border border-blue-700">
            <p className="text-xs text-blue-200">
              📝 หมายเหตุ: หลังจากสมัครสมาชิก กรุณารอ Admin อนุมัติบัญชีของคุณก่อนเข้าใช้งาน
              <br />
              Note: Please wait for admin approval after registration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
