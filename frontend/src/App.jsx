import React, { useState } from 'react'
import ConnectMailbox from './components/ConnectMailbox'
import RunCleanupButton from './components/RunCleanupButton'
import StatusCard from './components/StatusCard'
import ClusterResults from './components/ClusterResults'

export default function App() {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState({})
  const [results, setResults] = useState(null)

  const handleStatus = (data) => {
    setStatus({
      total: data && data.cluster_map ? Object.values(data.cluster_map).flat().length : 0,
      folders: data && data.folders ? Object.keys(data.folders).length : 0,
      timestamp: Date.now()
    })
    setResults(data)
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
            <ClusterResults folders={results?.folders} clusterMap={results?.cluster_map} />
          </>
        )}
    </div>
  )
}
