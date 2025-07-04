import React from 'react'

export default function ClusterResults({ folders, clusterMap }) {
  if (!folders || !clusterMap) return null
  return (
    <div className="mt-8">
      <h2 className="text-xl font-bold mb-4">Clustered Emails Preview</h2>
      <div className="grid gap-6 md:grid-cols-2">
        {Object.entries(folders).map(([folderName]) => (
          <div key={folderName} className="bg-white rounded shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg text-green-700">
                {folderName}
              </h3>
              <span className="text-xs text-gray-400 ml-2">Folder: {folderName}</span>
            </div>
            <ul className="divide-y divide-gray-200">
              {(clusterMap[folderName] || []).map(email => (
                <li key={email.id} className="py-2">
                  <div className="font-medium text-gray-800 text-base">{email.subject || '(No subject)'}</div>
                  <div className="text-sm text-gray-700 whitespace-pre-line" style={{fontFamily: 'monospace'}}>{email.snippet}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    From: {email.sender?.name || '(Unknown sender)'}
                    {email.sender?.email ? ` <${email.sender.email}>` : ''}
                  </div>
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
