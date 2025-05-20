import React, { useState } from 'react'
import axios from 'axios'

export default function RunCleanupButton({ user, onStatus }) {
  const [loading, setLoading] = useState(false)

  const runCleanup = async () => {
    setLoading(true)
    try {
      const resp = await axios.post('/api/email/run-cleanse')
      onStatus(resp.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <button
      disabled={loading}
      onClick={runCleanup}
      className="mt-4 px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
    >
      {loading ? 'Cleaning…' : 'Run Cleanup'}
    </button>
  )
}
