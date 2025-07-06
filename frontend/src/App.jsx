import React, { useState } from 'react';
import ConnectMailbox from './components/ConnectMailbox';
import ControlsPanel from './components/ControlsPanel';

export default function App() {
  const [user, setUser] = useState(null);

  return (
    <div className="min-h-screen flex items-start justify-center pt-[18vh] pb-[10vh] px-4">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-xl p-8 flex flex-col items-center gap-6">
        <h1 className="text-4xl font-bold text-haze-blue-1 text-center">Inbox Genie</h1>
        <p className="text-gray-600 text-center">Sort and manage your inbox with a single click</p>

        {!user ? (
          <ConnectMailbox onLogin={setUser} />
        ) : (
          <ControlsPanel user={user} />
        )}
      </div>
    </div>
  );
}
