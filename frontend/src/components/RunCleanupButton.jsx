import React, { useState } from 'react'
import axios from 'axios'

export default function RunCleanupButton({ user }) {
  const [loading, setLoading] = useState(false)
  const [catLoading, setCatLoading] = useState(false)
  const [undoLoading, setUndoLoading] = useState(false)
  const [numEmails, setNumEmails] = useState(50)
  const [resultMsg, setResultMsg] = useState("")

  const runCategorizeEmails = async () => {
    setCatLoading(true)
    setResultMsg("")
    try {
      const userEmail = user?.username || user?.email || user?.userName
      if (!userEmail) throw new Error('User email not found in user object')
      const resp = await axios.post('/api/email/emails/categorize', {
        user_email: userEmail,
        num_emails: numEmails
      })
      setResultMsg(resp.data.message || "Sorting complete!")
    } catch (err) {
      setResultMsg("Error: " + (err?.response?.data?.error || err.message))
    } finally {
      setCatLoading(false)
    }
  }

  const runUndo = async () => {
    setUndoLoading(true)
    setResultMsg("")
    try {
      const userEmail = user?.username || user?.email || user?.userName
      if (!userEmail) throw new Error('User email not found in user object')
      const resp = await axios.post('/api/email/emails/undo', {
        user_email: userEmail
      })
      setResultMsg(resp.data.message)
    } catch (err) {
      setResultMsg("Error: " + (err?.response?.data?.error || err.message))
    } finally {
      setUndoLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 mt-4 items-start">
      <div className="flex gap-4 items-center">
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
          disabled={catLoading}
          onClick={runCategorizeEmails}
          className="px-4 py-2 bg-blue-700 text-white rounded disabled:opacity-50"
        >
          {catLoading ? 'Sorting…' : 'Sort & Move Emails'}
        </button>
        <button
          disabled={undoLoading}
          onClick={runUndo}
          className="px-4 py-2 bg-gray-600 text-white rounded disabled:opacity-50"
        >
          {undoLoading ? 'Undoing…' : 'Undo Last Sort'}
        </button>
      </div>
      {resultMsg && (
        <div className="text-green-700 font-semibold bg-green-100 rounded px-4 py-2 mt-2">{resultMsg}</div>
      )}
    </div>
  )
}
