import React from 'react'

function statusBadge(status, inning, inningState) {
  const s = (status || '').toLowerCase()
  if (s.includes('progress') || s.includes('live')) {
    const label = inning ? `${inningState || ''} ${inning}`.trim() : 'Live'
    return <span className="badge badge-live">● {label}</span>
  }
  if (s.includes('final')) {
    return <span className="badge badge-final">Final</span>
  }
  return <span className="badge badge-upcoming">{status || 'Scheduled'}</span>
}

function marketTypeBadge(type) {
  const labels = { moneyline: 'ML', runline: 'RL', total: 'O/U', other: 'Mkt' }
  return <span className="badge badge-type">{labels[type] || type}</span>
}

export default function GameCard({ game }) {
  const {
    away_team,
    away_team_abbr,
    away_score,
    home_team,
    home_team_abbr,
    home_score,
    run_diff,
    status,
    inning,
    inning_state,
    game_time,
    kalshi_markets = [],
  } = game

  const isBlowout = run_diff >= 5
  const cardClass = isBlowout ? 'card blowout-card' : 'card'

  return (
    <div className={cardClass}>
      {/* Scoreboard */}
      <div className="scoreboard">
        <div className="team-block away">
          <span className="team-abbr">{away_team_abbr}</span>
          <span className="team-name">{away_team}</span>
        </div>
        <div className="score-block">
          <span className="score">{away_score}</span>
          <span className="score-sep">–</span>
          <span className="score">{home_score}</span>
        </div>
        <div className="team-block home">
          <span className="team-abbr">{home_team_abbr}</span>
          <span className="team-name">{home_team}</span>
        </div>
      </div>

      {/* Badges */}
      <div className="badge-row">
        {statusBadge(status, inning, inning_state)}
        {isBlowout && (
          <span className="badge badge-blowout">BLOWOUT 🔥 +{run_diff}</span>
        )}
      </div>

      {/* Game time for upcoming */}
      {!(status || '').toLowerCase().includes('progress') &&
        !(status || '').toLowerCase().includes('final') &&
        game_time && (
          <div className="game-time">{game_time}</div>
        )}

      {/* Kalshi markets */}
      {kalshi_markets.length > 0 && (
        <>
          <hr className="card-divider" />
          <div className="kalshi-section">
            <div className="kalshi-heading">Kalshi Markets</div>
            {kalshi_markets.map((market, idx) => (
              <div key={market.ticker || idx} className="market-item">
                <div className="market-title">
                  <span style={{ marginRight: '0.4rem' }}>{market.title}</span>
                  {marketTypeBadge(market.market_type)}
                  {market.is_shifted && (
                    <span className="badge badge-shifted" style={{ marginLeft: '0.3rem' }}>
                      ⚡ Shifted
                    </span>
                  )}
                </div>
                <div className="market-prices">
                  <span>
                    <span className="price-label">Yes</span>
                    <span className="price-yes">
                      {market.yes_bid.toFixed(2)} / {market.yes_ask.toFixed(2)}
                    </span>
                  </span>
                  <span>
                    <span className="price-label">No</span>
                    <span className="price-no">
                      {market.no_bid.toFixed(2)} / {market.no_ask.toFixed(2)}
                    </span>
                  </span>
                  {market.volume > 0 && (
                    <span style={{ color: '#475569', fontSize: '0.72rem' }}>
                      Vol: {market.volume.toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
