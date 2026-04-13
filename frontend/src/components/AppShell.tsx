import type { ReactNode } from 'react'

type AppShellProps = {
  title?: string
  /** Extra content aligned to the right of the title (e.g. actions). */
  headerRight?: ReactNode
  /** Larger page title (e.g. digest view). */
  titleLarge?: boolean
  children?: ReactNode
}

export function AppShell({
  title = 'Email Summarizer',
  headerRight,
  titleLarge = false,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <div className="app-shell__header-row">
          <h1
            className={
              titleLarge
                ? 'app-shell__title app-shell__title--large'
                : 'app-shell__title'
            }
          >
            {title}
          </h1>
          {headerRight ? (
            <div className="app-shell__header-actions">{headerRight}</div>
          ) : null}
        </div>
      </header>
      <main className="app-shell__main">{children}</main>
      <footer className="app-shell__footer">
        <span className="muted">React + TypeScript + Vite</span>
      </footer>
    </div>
  )
}
