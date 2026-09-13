import React from 'react';

const SCENARIOS = [
  {
    id: 'scenario_1_true_duplicate',
    num: '01',
    title: 'True Duplicate',
    desc: 'Two identical charges; internal context confirms one expected.',
    query: "Investigate Acme's billing complaint regarding duplicate $499 annual subscription charge.",
    customer: 'Acme Corp',
    email: 'alex@acmecorp.com'
  },
  {
    id: 'scenario_2_false_duplicate',
    num: '02',
    title: 'False Duplicate',
    desc: 'Second charge is a legitimate implementation fee.',
    query: "Investigate duplicate charge complaint of $499 for Acme Corp.",
    customer: 'Acme Corp',
    email: 'billing@acmecorp.com'
  },
  {
    id: 'scenario_3_single_charge',
    num: '03',
    title: 'Only One Charge',
    desc: 'Customer claims two charges; Stripe shows one.',
    query: "Globex Corp reports being charged twice for $499.",
    customer: 'Globex Corp',
    email: 'accounting@globex.com'
  },
  {
    id: 'scenario_4_already_refunded',
    num: '04',
    title: 'Already Refunded',
    desc: 'Existing refund detected in Stripe ledger.',
    query: "Follow up on duplicate charge dispute for Initech LLC.",
    customer: 'Initech LLC',
    email: 'finance@initech.com'
  },
  {
    id: 'scenario_5_conflicting_evidence',
    num: '05',
    title: 'Conflicting Slack',
    desc: 'Internal team members disagree in discussion.',
    query: "Review double billing dispute on Soylent Corp account.",
    customer: 'Soylent Corp',
    email: 'admin@soylent.com'
  },
  {
    id: 'scenario_6_stripe_failure',
    num: '06',
    title: 'Stripe Outage',
    desc: 'Financial ledger unreachable; fail-safe halt.',
    query: "Dispute investigation for Hooli subscription double billing.",
    customer: 'Hooli',
    email: 'ops@hooli.com'
  }
];

export default function ScenarioSelector({ onSelectScenario, onSelectCustomLive, currentScenarioId }) {
  return (
    <div style={{ marginBottom: '28px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="label-caps">Dispute Scenarios</div>
          {onSelectCustomLive && (
            <button
              type="button"
              className="btn-secondary"
              onClick={onSelectCustomLive}
              style={{
                padding: '3px 10px',
                fontSize: '0.72rem',
                fontWeight: '600',
                borderColor: currentScenarioId === null ? 'var(--success)' : 'var(--line)',
                color: currentScenarioId === null ? 'var(--success)' : 'var(--text)',
                borderRadius: 'var(--radius-sm)'
              }}
            >
              ● Custom Live Dispute
            </button>
          )}
        </div>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          Select a preset benchmark case or click Custom Live
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '8px' }}>
        {SCENARIOS.map((sc) => {
          const isSelected = currentScenarioId === sc.id;
          return (
            <button
              key={sc.id}
              onClick={() => onSelectScenario(sc)}
              style={{
                textAlign: 'left',
                padding: '12px 14px',
                borderRadius: 'var(--radius-sm)',
                background: isSelected ? 'var(--surface-secondary)' : 'var(--surface)',
                border: '1px solid',
                borderColor: isSelected ? 'var(--accent)' : 'var(--line)',
                borderLeftWidth: isSelected ? '3px' : '1px',
                borderLeftColor: isSelected ? 'var(--accent)' : 'var(--line)',
                cursor: 'pointer',
                outline: 'none',
                transition: 'all var(--duration-fast) var(--ease)',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
              }}
            >
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                fontWeight: '600',
                color: isSelected ? 'var(--accent)' : 'var(--text-muted)',
                marginTop: '1px'
              }}>
                {sc.num}
              </span>
              <div>
                <div style={{
                  fontSize: '0.82rem',
                  fontWeight: isSelected ? '600' : '500',
                  color: isSelected ? 'var(--text)' : 'var(--text-secondary)',
                  marginBottom: '2px'
                }}>
                  {sc.title}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: '1.35' }}>
                  {sc.desc}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
