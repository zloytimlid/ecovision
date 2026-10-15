import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as authApi from '../api/auth.js'
import { getToken, setToken, TOKEN_REJECTED_EVENT } from '../utils/authToken.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const [token, setTokenState] = useState(getToken)

  const me = useQuery({
    queryKey: ['me', token],
    queryFn: authApi.getMe,
    enabled: Boolean(token),
    staleTime: 60 * 1000,
  })

  // History and results depend on who is logged in, so drop all cached data.
  const switchToken = useCallback(
    (newToken) => {
      setToken(newToken)
      setTokenState(newToken)
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== 'categories' })
    },
    [queryClient],
  )

  useEffect(() => {
    const onRejected = () => switchToken(null)
    window.addEventListener(TOKEN_REJECTED_EVENT, onRejected)
    return () => window.removeEventListener(TOKEN_REJECTED_EVENT, onRejected)
  }, [switchToken])

  const value = useMemo(
    () => ({
      user: token ? me.data ?? null : null,
      isLoggedIn: Boolean(token),
      isLoading: Boolean(token) && me.isPending,
      async login(username, password) {
        const data = await authApi.login(username, password)
        switchToken(data.token)
        return data.user
      },
      async register(username, password) {
        const data = await authApi.register(username, password)
        switchToken(data.token)
        return data.user
      },
      async logout() {
        try {
          await authApi.logout()
        } catch {
          // The token is dropped locally even if the server is unreachable.
        }
        switchToken(null)
      },
    }),
    [token, me.data, me.isPending, switchToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default function useAuth() {
  return useContext(AuthContext)
}
