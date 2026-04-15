import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { loadTabLabels, saveTabLabels, type TabLabelMap } from '../utils/digestTabLabels'
import { pruneRedundantTabLabels } from '../utils/tabLabelDefaults'

type TabLabelsContextValue = {
  labels: TabLabelMap
  setLabels: (next: TabLabelMap) => void
}

const TabLabelsContext = createContext<TabLabelsContextValue | null>(null)

export function TabLabelsProvider({ children }: { children: ReactNode }) {
  const [labels, setLabelsState] = useState<TabLabelMap>(() => loadTabLabels())

  const setLabels = useCallback((next: TabLabelMap) => {
    const pruned = pruneRedundantTabLabels(next)
    setLabelsState(pruned)
    saveTabLabels(pruned)
  }, [])

  const value = useMemo(() => ({ labels, setLabels }), [labels, setLabels])

  return (
    <TabLabelsContext.Provider value={value}>{children}</TabLabelsContext.Provider>
  )
}

export function useTabLabels(): TabLabelsContextValue {
  const ctx = useContext(TabLabelsContext)
  if (!ctx) {
    throw new Error('useTabLabels must be used within TabLabelsProvider')
  }
  return ctx
}
