import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { fetchAccounts } from '../api/accounts'

type AccountsContextValue = {
  accounts: string[]
}

const AccountsContext = createContext<AccountsContextValue | null>(null)

export function AccountsProvider({ children }: { children: ReactNode }) {
  const [accounts, setAccounts] = useState<string[]>([])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await fetchAccounts()
        if (!cancelled) {
          setAccounts(data)
        }
      } catch {
        if (!cancelled) {
          setAccounts([])
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const value = useMemo(() => ({ accounts }), [accounts])

  return (
    <AccountsContext.Provider value={value}>{children}</AccountsContext.Provider>
  )
}

export function useAccounts(): AccountsContextValue {
  const ctx = useContext(AccountsContext)
  if (!ctx) {
    throw new Error('useAccounts must be used within AccountsProvider')
  }
  return ctx
}
