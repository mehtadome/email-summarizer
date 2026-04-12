import type { ReactNode } from 'react'

type AppShellProps = {
  title?: string
  children?: ReactNode
}

export function AppShell({
  title = 'Email summarizer',
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <h1 className="app-shell__title">{title}</h1>
      </header>
      <main className="app-shell__main">{children}</main>
      <footer className="app-shell__footer">
        <span className="muted">React + TypeScript + Vite</span>
      </footer>
    </div>
  )
}
