import React from 'react'
import { PublicClientApplication } from '@azure/msal-browser'

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID,
    redirectUri: window.location.origin
  }
}

export default function ConnectMailbox({ onLogin }) {
  const pca = new PublicClientApplication(msalConfig)

  const handleLogin = async () => {
    await pca.loginPopup({ scopes: ['Mail.ReadWrite'] })
    const account = pca.getAllAccounts()[0]
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
