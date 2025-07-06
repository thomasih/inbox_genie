import React, { useState } from 'react';
import axios from 'axios';

export default function ControlsPanel({ user }) {
  const [count, setCount] = useState(50);
  const [loading, setLoading] = useState(false);

  const handleSort = async () => {
    setLoading(true);
    try {
      await axios.post('/api/email/emails/categorize', {
        user_email: user.username || user.email,
        num_emails: count
      });
      // optionally show toast or update local state...
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = async () => {
    if (loading) return;
    await axios.post('/api/email/emails/undo', { user_email: user.username || user.email });
    // optionally show toast or update local state...
  };

  return (
    <div className="w-full bg-white border border-haze-blue-2 rounded-xl shadow-sm flex flex-col sm:flex-row items-center justify-between p-6 gap-4 relative">
      <div className="flex items-center gap-2">
        <label className="text-gray-700 font-medium">Emails:</label>
        <input
          type="number"
          min="1"
          value={count}
          onChange={e => setCount(e.target.value)}
          className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-haze-blue-3"
          disabled={loading}
        />
      </div>

      <button
        onClick={handleSort}
        className={`bg-haze-blue-2 hover:bg-haze-blue-3 text-white font-semibold py-3 px-6 rounded-xl shadow-md transition-all duration-200 flex items-center gap-2 ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
        disabled={loading}
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.5 10.5l3-3m0 0l3 3m-3-3v12" />
        </svg>
        Sort
      </button>

      <button
        onClick={handleUndo}
        className="bg-gray-200 hover:bg-gray-300 text-haze-blue-1 font-semibold py-3 px-6 rounded-xl shadow-sm transition-all duration-200 flex items-center gap-2"
        disabled={loading}
      >
        {/* Use a standard arrow-uturn-left icon for undo */}
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l-4-4m0 0l4-4m-4 4h12" />
        </svg>
        Undo
      </button>

      {loading && (
        <div className="absolute left-0 top-full w-full flex flex-col items-center mt-16 z-10">
          <span className="text-haze-blue-1 font-medium mb-2">This may take a few seconds...</span>
          <div className="w-2/3 h-2 bg-haze-blue-4 rounded-full overflow-hidden relative">
            <div className="loading-bar-animation absolute left-0 top-0 h-full w-1/3 bg-haze-blue-2 rounded-full" />
          </div>
        </div>
      )}
    </div>
  );
}
