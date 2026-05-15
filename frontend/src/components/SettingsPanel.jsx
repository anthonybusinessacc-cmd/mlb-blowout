import React, { useState, useEffect } from 'react'

export default function SettingsPanel({ settings }) {
  const [threshold, setThreshold] = useState(5)
  const [phoneNumber, setPhoneNumber] = useState('')
  const [smsEnabled, setSmsEnabled] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState(null) // { type: 'success'|'error', text: string }

  useEffect(() => {
    if (settings) {
      setThreshold(settings.threshold ?? 5)
      setPhoneNumber(settings.phone_number ?? '')
      setSmsEnabled(settings.sms_enabled ?? true)
    }
  }, [settings])

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setSaveMsg(null)
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          threshold: Number(threshold),
          phone_number: phoneNumber,
          sms_enabled: smsEnabled,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      setSaveMsg({ type: 'success', text: 'Settings saved successfully.' })
    } catch (err) {
      setSaveMsg({ type: 'error', text: `Failed to save: ${err.message}` })
    } finally {
      setSaving(false)
      setTimeout(() => setSaveMsg(null), 4000)
    }
  }

  return (
    <div className="settings-panel">
      <div className="settings-card">
        <div className="settings-title">Notification Settings</div>
        <form onSubmit={handleSave}>
          <div className="form-group">
            <label className="form-label" htmlFor="threshold">
              Blowout Run Differential Threshold
            </label>
            <input
              id="threshold"
              className="form-input"
              type="number"
              min={1}
              max={20}
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.3rem' }}>
              Alert when run differential reaches this number (default: 5)
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="phone">
              SMS Phone Number
            </label>
            <input
              id="phone"
              className="form-input"
              type="text"
              placeholder="+12125551234"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
            />
            <div style={{ fontSize: '0.75rem', color: '#475569', marginTop: '0.3rem' }}>
              Include country code (e.g. +1 for US). Leave blank to disable SMS.
            </div>
          </div>

          <div className="form-group">
            <div className="toggle-row">
              <input
                id="sms-toggle"
                className="toggle-checkbox"
                type="checkbox"
                checked={smsEnabled}
                onChange={(e) => setSmsEnabled(e.target.checked)}
              />
              <label className="toggle-label" htmlFor="sms-toggle">
                Enable SMS notifications
              </label>
            </div>
          </div>

          <button className="btn-save" type="submit" disabled={saving}>
            {saving ? 'Saving...' : 'Save Settings'}
          </button>

          {saveMsg && (
            <div className={`save-msg ${saveMsg.type}`}>{saveMsg.text}</div>
          )}
        </form>
      </div>
    </div>
  )
}
