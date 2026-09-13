import React, { useState } from 'react';
import { IconMail, IconStripe, IconSlack } from './Icons';

export default function EvidenceMatrix({ evidence = [] }) {
  const [activeSource, setActiveSource] = useState('gmail');

  const gmailItems = evidence.filter(e => e.source === 'gmail');
  const stripeCharges = evidence.filter(e => e.source === 'stripe' && e.evidence_type === 'charge');
  const stripeRefunds = evidence.filter(e => e.source === 'stripe' && e.evidence_type === 'refund');
  const slackItems = evidence.filter(e => e.source === 'slack');

  return (
    <div className="panel" style={{ padding: '24px', marginBottom: '28px' }}>
      
      {/* Section Header & Horizontal Source Selector */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid var(--line)' }}>
        <div>
          <div className="label-caps" style={{ marginBottom: '4px' }}>Evidence Dossier</div>
          <h3 className="heading-md">Normalized Multi-App Findings</h3>
        </div>

        {/* Source Navigation Tabs */}
        <div style={{ display: 'flex', gap: '4px', background: 'var(--surface-secondary)', padding: '3px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--line)' }}>
          <button
            onClick={() => setActiveSource('gmail')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: activeSource === 'gmail' ? 'var(--surface)' : 'transparent',
              color: activeSource === 'gmail' ? 'var(--text)' : 'var(--text-muted)',
              fontSize: '0.8rem',
              fontWeight: activeSource === 'gmail' ? '600' : '400',
              cursor: 'pointer',
              outline: 'none',
              boxShadow: activeSource === 'gmail' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
            }}
          >
            <IconMail size={14} />
            <span>Gmail</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>({gmailItems.length})</span>
          </button>

          <button
            onClick={() => setActiveSource('stripe')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: activeSource === 'stripe' ? 'var(--surface)' : 'transparent',
              color: activeSource === 'stripe' ? 'var(--text)' : 'var(--text-muted)',
              fontSize: '0.8rem',
              fontWeight: activeSource === 'stripe' ? '600' : '400',
              cursor: 'pointer',
              outline: 'none',
              boxShadow: activeSource === 'stripe' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
            }}
          >
            <IconStripe size={14} />
            <span>Stripe</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>({stripeCharges.length})</span>
          </button>

          <button
            onClick={() => setActiveSource('slack')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: activeSource === 'slack' ? 'var(--surface)' : 'transparent',
              color: activeSource === 'slack' ? 'var(--text)' : 'var(--text-muted)',
              fontSize: '0.8rem',
              fontWeight: activeSource === 'slack' ? '600' : '400',
              cursor: 'pointer',
              outline: 'none',
              boxShadow: activeSource === 'slack' ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
            }}
          >
            <IconSlack size={14} />
            <span>Slack</span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>({slackItems.length})</span>
          </button>
        </div>
      </div>

      {/* Content Area Based on Active Source */}
      
      {/* 1. GMAIL: Clean document presentation */}
      {activeSource === 'gmail' && (
        <div>
          {gmailItems.length === 0 ? (
            <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No customer email records found in Gmail.
            </div>
          ) : (
            gmailItems.map((item, idx) => {
              const p = item.payload || {};
              return (
                <div key={idx} style={{ maxWidth: '720px' }}>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '100px 1fr',
                    rowGap: '6px',
                    fontSize: '0.82rem',
                    marginBottom: '16px',
                    paddingBottom: '14px',
                    borderBottom: '1px solid var(--line-subtle)'
                  }}>
                    <span style={{ color: 'var(--text-muted)' }}>Subject:</span>
                    <strong style={{ color: 'var(--text)' }}>{p.subject}</strong>

                    <span style={{ color: 'var(--text-muted)' }}>From:</span>
                    <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>{p.sender}</span>

                    <span style={{ color: 'var(--text-muted)' }}>Date:</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{p.timestamp}</span>
                  </div>

                  <div style={{
                    fontSize: '0.88rem',
                    color: 'var(--text)',
                    lineHeight: '1.6',
                    marginBottom: '20px',
                    whiteSpace: 'pre-line'
                  }}>
                    {p.body}
                  </div>

                  {Array.isArray(p.relevant_claims) && p.relevant_claims.length > 0 && (
                    <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--line-subtle)' }}>
                      <div className="label-caps" style={{ marginBottom: '8px' }}>Parsed Claims:</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {p.relevant_claims.map((claim, cIdx) => (
                          <span
                            key={cIdx}
                            style={{
                              padding: '3px 8px',
                              background: 'var(--surface-secondary)',
                              border: '1px solid var(--line)',
                              borderRadius: 'var(--radius-sm)',
                              fontSize: '0.75rem',
                              color: 'var(--text-secondary)'
                            }}
                          >
                            {claim}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* 2. STRIPE: Clean transaction table */}
      {activeSource === 'stripe' && (
        <div>
          {stripeCharges.length === 0 ? (
            <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No Stripe transaction records found.
            </div>
          ) : (
            <div>
              <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--line)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px 12px', fontWeight: '500' }}>Charge ID</th>
                      <th style={{ padding: '8px 12px', fontWeight: '500' }}>Description</th>
                      <th style={{ padding: '8px 12px', fontWeight: '500' }}>Amount</th>
                      <th style={{ padding: '8px 12px', fontWeight: '500' }}>Status</th>
                      <th style={{ padding: '8px 12px', fontWeight: '500' }}>Refunded</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stripeCharges.map((item, idx) => {
                      const c = item.payload || {};
                      return (
                        <tr key={idx} style={{ borderBottom: '1px solid var(--line-subtle)' }}>
                          <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text)' }}>
                            {c.id}
                          </td>
                          <td style={{ padding: '12px', color: 'var(--text)' }}>
                            {c.description || 'Subscription Service'}
                          </td>
                          <td style={{ padding: '12px', fontWeight: '600', color: 'var(--text)' }}>
                            ${(Number(c.amount || 0) / 100).toFixed(2)} <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{c.currency?.toUpperCase() || 'USD'}</span>
                          </td>
                          <td style={{ padding: '12px' }}>
                            <span className="status-tag status-tag-success" style={{ fontSize: '0.68rem' }}>
                              {c.status || 'succeeded'}
                            </span>
                          </td>
                          <td style={{ padding: '12px', color: c.refunded ? 'var(--warning)' : 'var(--text-muted)' }}>
                            {c.refunded ? `Refunded ($${(Number(c.amount_refunded || 0) / 100).toFixed(2)})` : 'No'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {stripeRefunds.length > 0 && (
                <div style={{ background: 'var(--surface-secondary)', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)', padding: '12px 16px' }}>
                  <div className="label-caps" style={{ marginBottom: '6px' }}>Existing Stripe Refunds</div>
                  {stripeRefunds.map((rf, idx) => {
                    const r = rf.payload || {};
                    return (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontFamily: 'var(--font-mono)' }}>
                        <span style={{ color: 'var(--text)' }}>{r.id || 're_unknown'} (Charge {r.charge_id || 'ch_unknown'})</span>
                        <strong style={{ color: 'var(--warning)' }}>${(Number(r.amount || 0) / 100).toFixed(2)}</strong>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 3. SLACK: Clean conversation transcript */}
      {activeSource === 'slack' && (
        <div>
          {slackItems.length === 0 ? (
            <div style={{ padding: '32px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No internal Slack conversation found in #billing.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: '720px' }}>
              {slackItems.map((item, idx) => {
                const s = item.payload || {};
                return (
                  <div
                    key={idx}
                    style={{
                      borderLeft: '2px solid var(--line)',
                      paddingLeft: '14px',
                      paddingTop: '2px',
                      paddingBottom: '2px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: '600', color: 'var(--text)' }}>
                        @{s.author}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {s.channel} • {s.timestamp ? String(s.timestamp).substring(0, 10) : 'Recent'}
                      </span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                      {s.text}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
