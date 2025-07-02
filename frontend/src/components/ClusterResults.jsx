import React from 'react'

export default function ClusterResults({ folders, clusterMap }) {
  if (!folders || !clusterMap) return null
  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold mb-4">Clustered Emails Preview</h2>
      <div className="grid gap-6 md:grid-cols-2">
        {Object.entries(clusterMap).map(([clusterId, emails]) => (
          <div key={clusterId} className="bg-white rounded shadow p-4">
            <h3 className="font-semibold text-lg mb-2 text-green-700">
              {folders[clusterId] || `Cluster ${clusterId}`}
            </h3>
            <ul className="divide-y divide-gray-200">
              {emails.map(email => (
                <li key={email.id} className="py-2">
                  <div className="font-medium text-gray-800">{email.subject || '(No subject)'}</div>
                  <div className="text-xs text-gray-500 truncate">{email.body.slice(0, 120)}{email.body.length > 120 ? '…' : ''}</div>
                  <div className="text-[10px] text-gray-400 mt-1">ID: {email.id}</div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
