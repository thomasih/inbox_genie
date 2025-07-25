import React from 'react';
import { PublicClientApplication } from '@azure/msal-browser';
import axios from 'axios';

const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID,
    redirectUri: window.location.origin
  }
};

export default function ConnectMailbox({ onLogin }) {
  const pca = new PublicClientApplication(msalConfig);

  const handleLogin = async () => {
    const response = await pca.loginPopup({ scopes: ['Mail.ReadWrite'] });
    // Acquire the access token for Microsoft Graph
    const tokenResponse = await pca.acquireTokenSilent({
      scopes: ['Mail.ReadWrite'],
      account: response.account
    });
    // Send the access token to the backend
    await axios.post('/api/email/store-token', {
      user_email: response.account.username,
      access_token: tokenResponse.accessToken
      // Optionally: refresh_token, expires_at
    });
    onLogin(response.account);
  };

  return (
    <button
      onClick={handleLogin}
      className="w-full bg-haze-blue-2 hover:bg-haze-blue-3 text-white font-semibold py-3 rounded-xl shadow-md transition-all duration-200 flex items-center justify-center gap-2"
    >
      Connect Your Mailbox
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
      </svg>
    </button>
  );
}
