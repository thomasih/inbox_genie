import React, { useState } from 'react'
import ConnectMailbox from './components/ConnectMailbox'
import RunCleanupButton from './components/RunCleanupButton'
import StatusCard from './components/StatusCard'
import RawEmailResults from './components/RawEmailResults'

export default function App() {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState({})
  const [emails, setEmails] = useState(null)

  const handleStatus = (data) => {
    setStatus({
      total: data && data.emails ? data.emails.length : 0,
      timestamp: Date.now()
    })
    setEmails(data?.emails || [])
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <h1 className="text-3xl font-bold mb-6">InboxZen</h1>
      {!user
        ? <ConnectMailbox onLogin={setUser} />
        : (
          <>
            <StatusCard status={status} />
            <RunCleanupButton user={user} onStatus={handleStatus} />
            <RawEmailResults emails={emails} />
          </>
        )}
    </div>
  )
}
