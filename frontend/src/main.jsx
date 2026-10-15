import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './hooks/useAuth.jsx'
import { DeviceProvider } from './hooks/useDevice.jsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      // Do not retry 4xx errors (e.g. 404 for a deleted record).
      retry: (failureCount, error) => {
        const status = error?.response?.status
        return (!status || status >= 500) && failureCount < 1
      },
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <DeviceProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </DeviceProvider>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
