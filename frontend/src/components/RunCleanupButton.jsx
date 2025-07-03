import React, { useState } from 'react'
import axios from 'axios'

export default function RunCleanupButton({ user, onStatus }) {
  const [loading, setLoading] = useState(false)

  const runCleanup = async () => {
    setLoading(true)
    try {
      // Use the correct property for user email from MSAL account object
      const userEmail = user?.username || user?.email || user?.userName
      if (!userEmail) {
        throw new Error('User email not found in user object')
      }
      const resp = await axios.post('/api/email/run-cleanse', {
        user_email: userEmail,
        dry_run: true
      })
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
