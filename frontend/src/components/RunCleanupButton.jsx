import React, { useState } from 'react'
import axios from 'axios'

export default function RunCleanupButton({ user, onStatus }) {
  const [loading, setLoading] = useState(false)

  const runFetchRawEmails = async () => {
    setLoading(true)
    try {
      const userEmail = user?.username || user?.email || user?.userName
      if (!userEmail) {
        throw new Error('User email not found in user object')
      }
      const resp = await axios.post('/api/email/emails/raw', {
        user_email: userEmail
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
      onClick={runFetchRawEmails}
      className="mt-4 px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
    >
      {loading ? 'Fetching…' : 'Fetch Emails'}
    </button>
  )
}
