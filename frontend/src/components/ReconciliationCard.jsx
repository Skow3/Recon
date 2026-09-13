import React from 'react';
import { IconCheck, IconClose, IconAlert } from './Icons';

export default function ReconciliationCard({ reconciliation }) {
  if (!reconciliation) return null;

  const charges_found = Number(reconciliation.charges_found) || 0;
  const contradictions = Array.isArray(reconciliation.contradictions) ? reconciliation.contradictions : [];
  const supporting_evidence = Array.isArray(reconciliation.supporting_evidence) ? reconciliation.supporting_evidence : [];
  const refuting_evidence = Array.isArray(reconciliation.refuting_evidence) ? reconciliation.refuting_evidence : [];
  const risk_flags = Array.isArray(reconciliation.risk_flags) ? reconciliation.risk_flags : [];

  const hasContradictions = contradictions.length > 0;

  // Analytical Comparison Matrix
  const matrixRows = [
    {
      attribute: 'Customer identity verified',
      gmail: 'MATCH',
      stripe: 'MATCH',
      slack: 'MATCH'
    },
    {
      attribute: 'Charges recorded',
      gmail: '2 CLAIMED',
      stripe: `${charges_found} SETTLED`,
      slack: '—'
    },
    {
      attribute: 'Expected active charges',
      gmail: '—',
      stripe: '—',
      slack: hasContradictions ? '2 (FEE)' : '1 EXPECTED'
    },
    {
      attribute: 'Duplicate claim supported',
      gmail: 'REPORTED',
      stripe: charges_found >= 2 ? 'MATCH' : 'MISMATCH',
      slack: hasContradictions ? 'REFUTED' : 'CONFIRMED'
    },
    {
      attribute: 'Internal business agreement',
      gmail: '—',
      stripe: '—',
      slack: hasContradictions ? 'DOCUMENTED' : 'STANDARD'
    }
  ];

  return (
    <div className="panel" style={{ padding: '24px', marginBottom: '28px' }}>
      
      {/* Header */}
      <div style={{ marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid var(--line)' }}>
        <div className="label-caps" style={{ marginBottom: '4px' }}>Cross-System Reconciliation</div>
        <h3 className="heading-md" style={{ marginBottom: '4px' }}>
          What the systems agree on — and where they differ.
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Automated comparison of customer complaint, Stripe ledger transactions, and internal Slack communications.
        </p>
      </div>

      {/* Contradiction Alert Report (if any) */}
      {hasContradictions && (
        <div style={{
          padding: '16px',
          background: 'var(--danger-soft)',
          border: '1px solid rgba(180, 35, 24, 0.25)',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <IconAlert size={16} color="var(--danger)" />
            <span style={{ fontSize: '0.82rem', fontWeight: '600', color: 'var(--danger)' }}>
              Factual Contradiction Detected Across Subsystems
            </span>
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text)', lineHeight: '1.5' }}>
            {contradictions.map((c, idx) => (
              <p key={idx}>{c}</p>
            ))}
          </div>
        </div>
      )}

      {/* Analytical Comparison Table */}
      <div style={{ overflowX: 'auto', marginBottom: '24px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--line)', textAlign: 'left', color: 'var(--text-muted)' }}>
              <th style={{ padding: '8px 12px', fontWeight: '500' }}>Evaluation Dimension</th>
              <th style={{ padding: '8px 12px', fontWeight: '500' }}>Gmail</th>
              <th style={{ padding: '8px 12px', fontWeight: '500' }}>Stripe Ledger</th>
              <th style={{ padding: '8px 12px', fontWeight: '500' }}>Slack Context</th>
            </tr>
          </thead>
          <tbody>
            {matrixRows.map((row, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid var(--line-subtle)' }}>
                <td style={{ padding: '12px', color: 'var(--text)', fontWeight: '500' }}>
                  {row.attribute}
                </td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {row.gmail}
                </td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {row.stripe}
                </td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {row.slack}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Evidence Summary Rows */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Supporting evidence */}
        <div style={{ padding: '14px', background: 'var(--surface-secondary)', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)' }}>
          <div className="label-caps" style={{ color: 'var(--success)', marginBottom: '8px' }}>
            Supporting Evidence ({supporting_evidence.length})
          </div>
          {supporting_evidence.length === 0 ? (
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>No supporting evidence captured.</p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              {supporting_evidence.map((s, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{s}</li>
              ))}
            </ul>
          )}
        </div>

        {/* Refuting evidence */}
        <div style={{ padding: '14px', background: 'var(--surface-secondary)', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)' }}>
          <div className="label-caps" style={{ color: hasContradictions ? 'var(--danger)' : 'var(--text-muted)', marginBottom: '8px' }}>
            Contradicting / Refuting Evidence ({refuting_evidence.length})
          </div>
          {refuting_evidence.length === 0 ? (
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>None. Systems are in alignment.</p>
          ) : (
            <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              {refuting_evidence.map((r, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

    </div>
  );
}
