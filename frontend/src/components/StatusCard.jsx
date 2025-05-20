import React from 'react'

export default function StatusCard({ status }) {
  if (!status.total) return null
  return (
    <div className="mt-6 p-4 bg-white shadow rounded">
      <p><strong>Processed:</strong> {status.total} messages</p>
      <p><strong>Folders created:</strong> {status.folders}</p>
      <p><strong>Last run:</strong> {new Date(status.timestamp).toLocaleString()}</p>
    </div>
  )
}
