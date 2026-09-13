import React, { useState, useEffect } from 'react';
import {
  IconMail,
  IconStripe,
  IconSlack,
  IconCode,
  IconCalendar,
  IconFileText,
  IconDatabase,
  IconCheck,
  IconLayers,
  IconAlert,
  IconShield
} from './Icons';

export default function AppsView({ setNotification }) {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [testingApp, setTestingApp] = useState(null);
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    const fetchApps = async () => {
      try {
        setLoading(true);
        const res = await fetch('/api/apps');
        if (res.ok) {
          const data = await res.json();
          setApps(data.apps || []);
        }
      } catch (err) {
        console.error('Failed to load apps catalogue:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchApps();
  }, []);

  const handleTestConnection = async (appId) => {
    try {
      setTestingApp(appId);
      const res = await fetch(`/api/apps/${appId}/test-connection`, { method: 'POST' });
      const data = await res.json();
      setTestResults(prev => ({ ...prev, [appId]: data }));
      if (data.status === 'connected') {
        setNotification({ type: 'success', message: `${data.app_id.toUpperCase()} connection verified: ${data.message}` });
      } else {
        setNotification({ type: 'warning', message: `${data.app_id.toUpperCase()} notice: ${data.message}` });
      }
    } catch (err) {
      setNotification({ type: 'error', message: `Test failed for ${appId}: ${err.message}` });
    } finally {
      setTestingApp(null);
    }
  };

  const getAppIcon = (appId) => {
    switch (appId) {
      case 'gmail': return <IconMail size={22} />;
      case 'stripe': return <IconStripe size={22} />;
      case 'slack': return <IconSlack size={22} />;
      case 'github': return <IconCode size={22} />;
      case 'google_calendar': return <IconCalendar size={22} />;
      case 'google_drive': return <IconFileText size={22} />;
      case 'notion': return <IconDatabase size={22} />;
      case 'linear': return <IconCheck size={22} />;
      case 'jira': return <IconLayers size={22} />;
      default: return <IconLayers size={22} />;
    }
  };

  return (
    <div>
      {/* Header Section */}
      <section style={{ marginBottom: '32px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 10px', background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
          <span className="status-dot status-dot-accent"></span>
          <span className="label-caps" style={{ color: 'var(--text-secondary)' }}>
            App Connection Center
          </span>
        </div>

        <h1 className="heading-lg" style={{ marginBottom: '12px' }}>
          Connected Subsystems & Platform Ecosystem
        </h1>
        <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', maxWidth: '680px', margin: 0, lineHeight: '1.5' }}>
          RECON coordinates multi-app agents across authenticated tools with explicit permission isolation. Workspaces can only invoke tools corresponding to their assigned apps.
        </p>
      </section>

      {/* Security Architecture Summary Strip */}
      <div className="panel" style={{ padding: '20px 24px', marginBottom: '32px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ color: 'var(--accent)', marginTop: '2px' }}><IconShield size={18} /></div>
            <div>
              <div style={{ fontSize: '0.84rem', fontWeight: '600', color: 'var(--text)', marginBottom: '4px' }}>
                Strict Security Boundaries
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                Tool calls are strictly validated against workspace boundaries at runtime. Non-financial workspaces cannot trigger Stripe.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ color: 'var(--warning)', marginTop: '2px' }}><IconAlert size={18} /></div>
            <div>
              <div style={{ fontSize: '0.84rem', fontWeight: '600', color: 'var(--text)', marginBottom: '4px' }}>
                Human-in-the-Loop Gating
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                Financial actions (e.g. Stripe refunds) require explicit human authorization before execution in TEST mode.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ color: 'var(--success)', marginTop: '2px' }}><IconCheck size={18} /></div>
            <div>
              <div style={{ fontSize: '0.84rem', fontWeight: '600', color: 'var(--text)', marginBottom: '4px' }}>
                Event Deduplication Ledger
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                Every ingested event is cryptographically indexed in SQLite. Duplicate notifications are suppressed.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Apps Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {apps.map(app => {
          const isConnected = app.connected;
          const isComingSoon = app.status === 'coming_soon';
          const testResult = testResults[app.app_id];

          return (
            <div
              key={app.app_id}
              className="panel"
              style={{
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                opacity: isComingSoon ? 0.85 : 1
              }}
            >
              <div>
                {/* Top Row: Icon, Title & Status */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ color: 'var(--text)' }}>
                      {getAppIcon(app.app_id)}
                    </div>
                    <div>
                      <h3 style={{ fontSize: '0.98rem', fontWeight: '600', color: 'var(--text)', margin: 0 }}>
                        {app.name}
                      </h3>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {app.category}
                      </span>
                    </div>
                  </div>

                  {isConnected ? (
                    <span className="status-tag status-tag-success" style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                      <span className="status-dot status-dot-success" style={{ width: '5px', height: '5px' }}></span>
                      Connected
                    </span>
                  ) : isComingSoon ? (
                    <span className="status-tag status-tag-neutral" style={{ fontSize: '0.68rem' }}>
                      Coming Soon
                    </span>
                  ) : (
                    <span className="status-tag status-tag-neutral" style={{ fontSize: '0.68rem' }}>
                      Available
                    </span>
                  )}
                </div>

                {/* Description */}
                <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.45', marginBottom: '16px' }}>
                  {app.description}
                </p>

                {/* Supported Events */}
                {app.supported_events?.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '0.68rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                      Triggers & Events
                    </div>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {app.supported_events.map(ev => (
                        <span key={ev} style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.68rem',
                          background: 'var(--surface-secondary)',
                          border: '1px solid var(--line)',
                          padding: '1px 6px',
                          borderRadius: 'var(--radius-sm)',
                          color: 'var(--text-muted)'
                        }}>
                          {ev}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Available Actions */}
                {app.available_actions?.length > 0 && (
                  <div style={{ marginBottom: '16px' }}>
                    <div style={{ fontSize: '0.68rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '4px' }}>
                      Tool Actions
                    </div>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                      {app.available_actions.map(act => (
                        <span key={act} style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.68rem',
                          background: 'var(--surface-secondary)',
                          border: '1px solid var(--line)',
                          padding: '1px 6px',
                          borderRadius: 'var(--radius-sm)',
                          color: 'var(--text)'
                        }}>
                          {act}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Bottom Test Connection */}
              <div style={{ borderTop: '1px solid var(--line)', paddingTop: '14px', marginTop: '10px' }}>
                {!isComingSoon ? (
                  <div>
                    <button
                      className="btn-secondary"
                      onClick={() => handleTestConnection(app.app_id)}
                      disabled={testingApp === app.app_id}
                      style={{ fontSize: '0.78rem', padding: '5px 10px', width: '100%' }}
                    >
                      {testingApp === app.app_id ? 'Checking API...' : 'Test Connection'}
                    </button>
                    {testResult && (
                      <div style={{
                        marginTop: '8px',
                        fontSize: '0.72rem',
                        color: testResult.status === 'connected' ? 'var(--success)' : 'var(--text-muted)',
                        lineHeight: '1.4'
                      }}>
                        {testResult.message}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textAlign: 'center' }}>
                    Connector scheduled for release
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
