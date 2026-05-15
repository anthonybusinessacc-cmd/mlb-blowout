import React, { useState, useEffect, useCallback } from 'react'
import GameCard from './components/GameCard'
import SettingsPanel from './components/SettingsPanel'
import NotificationLog from './components/NotificationLog'

const REFRESH_INTERVAL = 30_000 // 30 seconds
const FRESH_THRESHOLD = 35_000  // 35 seconds

export default function App() {
  const [games, setGames] = useState([])
  const [notifications, setNotifications] = useState([])
  const [settings, setSettings] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [activeTab, setActiveTab] = useState('games')
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    try {
      const [gamesRes, notifsRes, settingsRes] = await Promise.all([
        fetch('/api/games'),
        fetch('/api/notifications'),
        fetch('/api/settings'),
      ])

      if (gamesRes.ok) {
        const data = await gamesRes.json()
        // Sort: blowout games first (run_diff desc), then by status (live > final > other)
        data.sort((a, b) => {
          const statusScore = (s) => {
            const sl = (s || '').toLowerCase()
            if (sl.includes('progress')) return 2
            if (sl.includes('final')) return 1
            return 0
          }
          if (b.run_diff !== a.run_diff) return b.run_diff - a.run_diff
          return statusScore(b.status) - statusScore(a.status)
        })
        setGames(data)
      }

      if (notifsRes.ok) {
        setNotifications(await notifsRes.json())
      }

      if (settingsRes.ok) {
        setSettings(await settingsRes.json())
      }

      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      setError('Unable to reach backend. Is it running?')
    }
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchAll])

  const isFresh = lastUpdated && Date.now() - lastUpdated.getTime() < FRESH_THRESHOLD

  function formatTime(date) {
    if (!date) return '—'
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const blowoutCount = games.filter((g) => g.run_diff >= (settings?.threshold ?? 5)).length
  const liveCount = games.filter((g) =>
    (g.status || '').toLowerCase().includes('progress')
  ).length

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1 className="header-title">⚾ MLB Blowout Tracker</h1>
        <div className="header-meta">
          <span
            className={`pulse-dot ${isFresh ? 'active' : 'stale'}`}
            title={isFresh ? 'Data is fresh' : 'Data may be stale'}
          />
          <span>
            {liveCount > 0 && (
              <span style={{ color: '#4ade80', marginRight: '0.5rem' }}>
                {liveCount} live
              </span>
            )}
            {blowoutCount > 0 && (
              <span style={{ color: '#f87171', marginRight: '0.5rem' }}>
                {blowoutCount} blowout{blowoutCount !== 1 ? 's' : ''}
              </span>
            )}
            Updated {formatTime(lastUpdated)}
          </span>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div
          style={{
            background: '#7f1d1d',
            color: '#fca5a5',
            padding: '0.6rem 1rem',
            borderRadius: '8px',
            marginBottom: '1rem',
            fontSize: '0.85rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Tab bar */}
      <nav className="tab-bar">
        {['games', 'settings', 'notifications'].map((tab) => (
          <button
            key={tab}
            className={`tab${activeTab === tab ? ' tab-active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'games' && `Games${games.length > 0 ? ` (${games.length})` : ''}`}
            {tab === 'settings' && 'Settings'}
            {tab === 'notifications' &&
              `Notifications${notifications.length > 0 ? ` (${notifications.length})` : ''}`}
          </button>
        ))}
      </nav>

      {/* Tab content */}
      {activeTab === 'games' && (
        <div>
          {games.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">⚾</div>
              <div>No games today (or backend is starting up)</div>
              <div style={{ fontSize: '0.8rem', marginTop: '0.4rem', color: '#334155' }}>
                Data refreshes every 30 seconds
              </div>
            </div>
          ) : (
            <div className="game-grid">
              {games.map((game) => (
                <GameCard key={game.game_pk} game={game} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <SettingsPanel settings={settings} />
      )}

      {activeTab === 'notifications' && (
        <NotificationLog notifications={notifications} />
      )}
    </div>
  )
}
