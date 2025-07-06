import React, { useState } from 'react'
import axios from 'axios'

export default function RunCleanupButton({ user, onStatus, onCategorized }) {
  const [loading, setLoading] = useState(false)
  const [catLoading, setCatLoading] = useState(false)
  const [numEmails, setNumEmails] = useState(50)

  const runFetchRawEmails = async () => {
    setLoading(true)
    try {
      const userEmail = user?.username || user?.email || user?.userName
      if (!userEmail) {
        throw new Error('User email not found in user object')
      }
      const resp = await axios.post('/api/email/emails/raw', {
        user_email: userEmail,
        num_emails: numEmails
      })
      onStatus(resp.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const runCategorizeEmails = async () => {
    setCatLoading(true)
    try {
      const userEmail = user?.username || user?.email || user?.userName
      if (!userEmail) {
        throw new Error('User email not found in user object')
      }
      const resp = await axios.post('/api/email/emails/categorize', {
        user_email: userEmail,
        num_emails: numEmails
      })
      if (onCategorized) onCategorized(resp.data.folders)
    } catch (err) {
      console.error(err)
    } finally {
      setCatLoading(false)
    }
  }

  return (
    <div className="flex gap-4 mt-4 items-center">
      <label className="text-sm font-medium"># Emails:
        <input
          type="number"
          min={1}
          max={500}
          value={numEmails}
          onChange={e => setNumEmails(Number(e.target.value))}
          className="ml-2 w-20 px-2 py-1 border rounded"
        />
      </label>
      <button
        disabled={loading}
        onClick={runFetchRawEmails}
        className="px-4 py-2 bg-green-600 text-white rounded disabled:opacity-50"
      >
        {loading ? 'Fetching…' : 'Fetch Emails'}
      </button>
      <button
        disabled={catLoading}
        onClick={runCategorizeEmails}
        className="px-4 py-2 bg-blue-700 text-white rounded disabled:opacity-50"
      >
        {catLoading ? 'Categorizing…' : 'Categorize with LLM'}
      </button>
    </div>
  )
}
