import React, { useState } from 'react'
import ConnectMailbox from './components/ConnectMailbox'
import RunCleanupButton from './components/RunCleanupButton'
import StatusCard from './components/StatusCard'

export default function App() {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState({})

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <h1 className="text-3xl font-bold mb-6">Inbox Genie</h1>
      {!user
        ? <ConnectMailbox onLogin={setUser} />
        : (
          <>
            <StatusCard status={status} />
            <RunCleanupButton user={user} />
          </>
        )}
    </div>
  )
}
