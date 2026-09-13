import React, { useState, useEffect } from 'react';
import { IconChevronDown } from './Icons';

export default function AuditTab({ currentCaseId }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState(currentCaseId || '');
  const [expandedLogId, setExpandedLogId] = useState(null);

  useEffect(() => {
    fetch('/api/cases')
      .then(res => res.json())
      .then(data => {
        setCases(data);
        if (!selectedCaseId && data.length > 0) {
          setSelectedCaseId(data[0].id);
        }
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!selectedCaseId) return;
    setLoading(true);
    fetch(`/api/cases/${selectedCaseId}/audit`)
      .then(res => res.json())
      .then(data => setLogs(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedCaseId]);

  const toggleExpand = (id) => {
    setExpandedLogId(expandedLogId === id ? null : id);
  };

  const formatTime = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toTimeString().split(' ')[0];
    } catch {
      return isoString;
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '32px', paddingBottom: '20px', borderBottom: '1px solid var(--line)' }}>
        <div>
          <div className="label-caps" style={{ marginBottom: '6px' }}>System Audit Ledger</div>
          <h1 className="heading-lg" style={{ marginBottom: '6px' }}>Audit Trail</h1>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            Immutable chronological record of investigation state transitions, evidence captures, decisions, and financial operations.
          </p>
        </div>

        {cases.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Case:</span>
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              style={{
                background: 'var(--surface)',
                border: '1px solid var(--line)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 12px',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text)',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {cases.map(c => (
                <option key={c.id} value={c.id}>
                  {c.id} — {c.customer_name || 'Case'}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {loading ? (
        <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Loading audit events...
        </div>
      ) : logs.length === 0 ? (
        <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          No audit records found for this case.
        </div>
      ) : (
        <div className="panel" style={{ padding: '0', overflow: 'hidden' }}>
          
          <div style={{ padding: '12px 20px', borderBottom: '1px solid var(--line)', background: 'var(--surface-secondary)', fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
            <span>Event Timeline ({logs.length} events recorded)</span>
            <span>Case ID: {selectedCaseId}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {logs.map((log) => {
              const isExpanded = expandedLogId === log.id;
              const hasDetails = log.details && Object.keys(log.details).length > 0;

              return (
                <div
                  key={log.id}
                  style={{
                    borderBottom: '1px solid var(--line-subtle)',
                    transition: 'background-color var(--duration-fast) var(--ease)'
                  }}
                >
                  <div
                    onClick={() => hasDetails && toggleExpand(log.id)}
                    style={{
                      padding: '12px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: hasDetails ? 'pointer' : 'default',
                      userSelect: 'none',
                      background: isExpanded ? 'var(--surface-secondary)' : 'transparent'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', minWidth: '65px' }}>
                        {formatTime(log.timestamp)}
                      </span>

                      <div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', fontWeight: '600', color: 'var(--text)' }}>
                          {log.event_type}
                        </span>

                        {log.state_from && log.state_to && (
                          <span style={{ marginLeft: '12px', fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {log.state_from} → <strong style={{ color: 'var(--text)' }}>{log.state_to}</strong>
                          </span>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {hasDetails && (
                        <div style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s', color: 'var(--text-muted)' }}>
                          <IconChevronDown size={14} />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Developer-style code block */}
                  {isExpanded && hasDetails && (
                    <div style={{ padding: '0 20px 16px 20px', background: 'var(--surface-secondary)' }}>
                      <pre style={{
                        background: '#0D0D0D',
                        color: '#C8C8C2',
                        padding: '14px',
                        borderRadius: 'var(--radius-sm)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.72rem',
                        lineHeight: '1.5',
                        overflowX: 'auto',
                        border: '1px solid #242424'
                      }}>
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

        </div>
      )}

    </div>
  );
}
