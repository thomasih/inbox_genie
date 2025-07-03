import React from 'react'
import { PublicClientApplication } from '@azure/msal-browser'
import axios from 'axios'

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID,
    redirectUri: window.location.origin
  }
}

export default function ConnectMailbox({ onLogin }) {
  const pca = new PublicClientApplication(msalConfig)

  const handleLogin = async () => {
    const loginResponse = await pca.loginPopup({ scopes: ['Mail.ReadWrite'] })
    const account = pca.getAllAccounts()[0]
    // Acquire token after login
    const tokenResponse = await pca.acquireTokenSilent({
      scopes: ['Mail.ReadWrite'],
      account
    })
    // Store token in backend
    await axios.post('/api/email/store-token', {
      user_email: account.username,
      access_token: tokenResponse.accessToken
    })
    onLogin(account)
  }

  return (
    <button
      onClick={handleLogin}
      className="px-4 py-2 bg-blue-600 text-white rounded"
    >
      Connect your mailbox
    </button>
  )
}
