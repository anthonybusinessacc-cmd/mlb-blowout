import React from 'react'

function formatLocalTime(isoStr) {
  if (!isoStr) return ''
  try {
    const dt = new Date(isoStr)
    return dt.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: 'America/Los_Angeles',
    })
  } catch {
    return isoStr
  }
}

function extractGameLabel(message) {
  // Try to extract "TEAM1 X - TEAM2 Y" from the message
  const match = message.match(/:\s*(.+?)\s*\(/)
  if (match) return match[1].trim()
  return '—'
}

export default function NotificationLog({ notifications }) {
  if (!notifications || notifications.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔔</div>
        <div>No notifications sent today</div>
        <div style={{ fontSize: '0.8rem', marginTop: '0.4rem', color: '#334155' }}>
          Blowout alerts will appear here when triggered
        </div>
      </div>
    )
  }

  // Newest first (already sorted by backend, but ensure)
  const sorted = [...notifications].sort((a, b) =>
    (b.sent_at || '').localeCompare(a.sent_at || '')
  )

  return (
    <div className="notif-table-wrap">
      <table className="notif-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Game</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((n, idx) => (
            <tr key={n.id || idx}>
              <td className="notif-time">{formatLocalTime(n.sent_at)}</td>
              <td style={{ whiteSpace: 'nowrap', color: '#94a3b8', fontSize: '0.8rem' }}>
                {extractGameLabel(n.message)}
              </td>
              <td className="notif-message">{n.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
