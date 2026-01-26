/**
 * HouseSelector.jsx
 * Phase R.4 - House Selection Component
 * 
 * Displays list of houses user has membership to.
 * Calls POST /api/resident/select-house on selection.
 * 
 * Props:
 * - houses: Array of { house_id, house_code, village_name?, role? }
 * - onSelect: Function to call when house is selected
 * - loading: Boolean for loading state
 * - error: Error message to display
 */

import { Home, Loader2, ChevronRight } from 'lucide-react';

export default function HouseSelector({ houses, onSelect, loading, error }) {
  if (!houses || houses.length === 0) {
    return (
      <div className="text-center py-8">
        <Home className="mx-auto text-gray-600 mb-4" size={48} />
        <p className="text-gray-400">ไม่พบบ้านที่ลงทะเบียน</p>
        <p className="text-gray-500 text-sm mt-2">กรุณาติดต่อผู้ดูแลระบบ</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      <div className="text-center mb-4">
        <Home className="mx-auto text-emerald-500 mb-2" size={32} />
        <h3 className="text-lg text-white font-medium">เลือกบ้านที่ต้องการ</h3>
        <p className="text-gray-400 text-sm">คุณมีสิทธิ์เข้าถึง {houses.length} บ้าน</p>
      </div>
      
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-3 text-red-400 text-sm text-center">
          {error}
        </div>
      )}
      
      <div className="space-y-3">
        {houses.map((house) => (
          <button
            key={house.house_id}
            onClick={() => onSelect(house.house_id)}
            disabled={loading}
            className="w-full bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl p-4 text-left transition-colors flex items-center gap-4 group"
          >
            <div className="w-12 h-12 bg-emerald-600/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <Home className="text-emerald-500" size={24} />
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="text-white font-medium text-lg">
                บ้านเลขที่ {house.house_code}
              </p>
              {house.village_name && (
                <p className="text-gray-400 text-sm truncate">
                  {house.village_name}
                </p>
              )}
              {house.role && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded">
                  {house.role === 'owner' ? 'เจ้าของบ้าน' : 
                   house.role === 'tenant' ? 'ผู้เช่า' : 
                   house.role === 'family' ? 'สมาชิกในครอบครัว' : house.role}
                </span>
              )}
            </div>
            
            <ChevronRight className="text-gray-500 group-hover:text-white transition-colors flex-shrink-0" size={20} />
          </button>
        ))}
      </div>
      
      {loading && (
        <div className="flex items-center justify-center gap-2 text-gray-400 py-4">
          <Loader2 className="animate-spin" size={20} />
          <span>กำลังดำเนินการ...</span>
        </div>
      )}
    </div>
  );
}
