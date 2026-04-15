import type { ReactNode } from 'react'
import { SettingsGearLink } from './SettingsGearLink'

type AppShellProps = {
  title?: string
  /** Shown immediately next to the title (e.g. home refresh). */
  titleAccessory?: ReactNode
  /** Extra content to the left of the settings gear (e.g. digest actions). */
  headerRight?: ReactNode
  /** Larger page title (e.g. digest view). */
  titleLarge?: boolean
  children?: ReactNode
}

export function AppShell({
  title = 'Email Summarizer',
  titleAccessory,
  headerRight,
  titleLarge = false,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <div className="app-shell__header-row">
          <div className="app-shell__title-cluster">
            <h1
              className={
                titleLarge
                  ? 'app-shell__title app-shell__title--large'
                  : 'app-shell__title'
              }
            >
              {title}
            </h1>
            {titleAccessory}
          </div>
          <div className="app-shell__header-actions">
            {headerRight}
            <SettingsGearLink />
          </div>
        </div>
      </header>
      <main className="app-shell__main">{children}</main>
      <footer className="app-shell__footer">
        <span className="muted">React + TypeScript + Vite</span>
      </footer>
    </div>
  )
}
