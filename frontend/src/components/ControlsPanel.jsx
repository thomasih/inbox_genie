import React, { useState } from 'react';
import axios from 'axios';

function getFriendlyErrorMessage(msg) {
  if (!msg) return 'An unknown error occurred.';
  if (msg.includes('InvalidAuthenticationToken') || msg.includes('JWT is not well formed')) {
    return 'Your session has expired or authentication failed. Please reconnect your mailbox.';
  }
  if (msg.includes('Failed to fetch messages: status=401')) {
    return 'Authentication error. Please reconnect your mailbox.';
  }
  if (msg.length > 200) {
    return 'An error occurred while processing your request. Please try again or reconnect your mailbox.';
  }
  return msg;
}

function LoadingBar() {
  return (
    <div className="w-full flex justify-center mt-2">
      <div className="relative w-40 h-2 bg-gray-200 rounded overflow-hidden">
        <div className="absolute left-0 top-0 h-2 w-1/3 bg-haze-blue-2 animate-loading-bar" />
      </div>
      <style>{`
        @keyframes loadingBar {
          0% { left: 0; width: 30%; }
          50% { left: 70%; width: 30%; }
          100% { left: 0; width: 30%; }
        }
        .animate-loading-bar {
          animation: loadingBar 1.2s infinite cubic-bezier(0.4,0,0.2,1);
        }
      `}</style>
    </div>
  );
}

export default function ControlsPanel({ user }) {
  const [count, setCount] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingMsg, setLoadingMsg] = useState("");

  const handleSort = async () => {
    if (count > 50) {
      setError('Maximum number of emails that can be organised at once is 50.');
      setCount(50);
      return;
    }
    setLoading(true);
    setError("");
    setSuccess("");
    setLoadingMsg("Sorting emails...");
    try {
      const resp = await axios.post('/api/email/emails/categorize', {
        user_email: user.username || user.email,
        num_emails: count
      });
      if (resp.data && resp.data.message) {
        setSuccess(resp.data.message);
      } else {
        setSuccess('Emails sorted. Please check your inbox.');
      }
    } catch (e) {
      let msg = '';
      if (e.response && e.response.data && e.response.data.error) {
        msg = e.response.data.error;
        msg = msg.replace(/organized/g, 'organised').replace(/Organized/g, 'Organised');
      } else if (e.message) {
        msg = e.message;
      } else {
        msg = 'An error occurred while sorting emails.';
      }
      setError(getFriendlyErrorMessage(msg));
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  };

  const handleUndo = async () => {
    if (loading) return;
    setError("");
    setSuccess("");
    setLoading(true);
    setLoadingMsg("Undoing last sort...");
    try {
      const resp = await axios.post('/api/email/emails/undo', { user_email: user.username || user.email });
      if (resp.data && resp.data.message) {
        setSuccess(resp.data.message);
      } else {
        setSuccess('Undo complete. Please check your inbox.');
      }
    } catch (e) {
      let msg = '';
      if (e.response && e.response.data && e.response.data.error) {
        msg = e.response.data.error;
      } else if (e.message) {
        msg = e.message;
      } else {
        msg = 'An error occurred while undoing.';
      }
      setError(getFriendlyErrorMessage(msg));
    } finally {
      setLoading(false);
      setLoadingMsg("");
    }
  };

  return (
    <>
      <div className="w-full bg-white border border-haze-blue-2 rounded-xl shadow-sm flex flex-col sm:flex-row items-center justify-between p-6 gap-4 relative">
        <div className="flex items-center gap-2">
          <label className="text-gray-700 font-medium">Emails:</label>
          <input
            type="number"
            min={1}
            max={50}
            value={count}
            onChange={e => {
              let val = parseInt(e.target.value, 10);
              if (val > 50) {
                setError('Maximum number of emails that can be organised at once is 50.');
                val = 50;
              } else {
                setError("");
              }
              setCount(val);
            }}
            className="w-20 border rounded px-2 py-1 text-center"
            disabled={loading}
          />
        </div>
        <button
          onClick={handleSort}
          className="bg-haze-blue-2 hover:bg-haze-blue-3 text-white font-semibold py-2 px-6 rounded-xl shadow-md transition-all duration-200"
          disabled={loading}
        >
          Sort Emails
        </button>
        <button
          onClick={handleUndo}
          className="bg-gray-200 hover:bg-gray-300 text-haze-blue-2 font-semibold py-2 px-6 rounded-xl shadow-md transition-all duration-200"
          disabled={loading}
        >
          Undo
        </button>
      </div>
      {loading && (
        <>
          <div className="w-full text-center text-haze-blue-2 mt-2 text-sm">{loadingMsg}</div>
          <LoadingBar />
        </>
      )}
      {error && !loading && (
        <div className="w-full text-center text-red-600 mt-2 text-sm">{error}</div>
      )}
      {success && !error && !loading && (
        <div className="w-full text-center text-green-700 mt-2 text-sm">{success}</div>
      )}
    </>
  );
}
