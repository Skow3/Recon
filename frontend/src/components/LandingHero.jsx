import React from 'react';
import { ReconLogo, IconArrowRight, IconMail, IconStripe, IconSlack, IconShield, IconCheck, IconGrid, IconBriefcase, IconLayers } from './Icons';

export default function LandingHero({ onOpenWorkspaces, onStartInvestigation, onOpenApps, onViewEvaluation }) {
  const handleOpen = onOpenWorkspaces || onStartInvestigation;
  return (
    <div style={{ paddingBottom: '60px' }}>
      
      {/* Editorial Hero Header */}
      <section style={{ paddingTop: '64px', paddingBottom: '72px', maxWidth: '820px' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '4px 10px', background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 'var(--radius-sm)', marginBottom: '24px' }}>
          <span className="status-dot status-dot-accent"></span>
          <span className="label-caps" style={{ color: 'var(--text-secondary)' }}>
            Multi-App AI Agent Workspace Platform
          </span>
        </div>

        <h1 className="heading-xl" style={{ marginBottom: '20px', color: 'var(--text)', letterSpacing: '-0.03em' }}>
          Connect your apps.<br />
          Define what matters.<br />
          <span style={{ color: 'var(--text-muted)' }}>Let your agent handle the rest.</span>
        </h1>

        <p style={{ fontSize: '1.15rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '32px', maxWidth: '660px' }}>
          RECON deploys specialized AI agents across Gmail, Stripe, Slack, and your developer stack. Agents operate inside strict workspace security boundaries, reconcile contradictory evidence, eliminate noise, and enforce deterministic approval gates.
        </p>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
          <button
            className="btn-primary"
            onClick={handleOpen}
            style={{ padding: '12px 24px', fontSize: '0.92rem' }}
          >
            Explore Workspaces
            <IconArrowRight size={16} />
          </button>
          
          <button
            className="btn-secondary"
            onClick={onOpenApps}
            style={{ padding: '12px 20px', fontSize: '0.92rem' }}
          >
            App Integrations
          </button>

          <button
            className="btn-secondary"
            onClick={onViewEvaluation}
            style={{ padding: '12px 20px', fontSize: '0.92rem' }}
          >
            Reliability Benchmarks
          </button>
        </div>
      </section>

      {/* Three Connected Systems */}
      <section style={{ marginBottom: '64px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div className="label-caps">Connected Subsystems</div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Three independent sources of truth</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {/* Gmail */}
          <div className="panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <div style={{ color: 'var(--text-secondary)' }}><IconMail size={20} /></div>
              <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text)' }}>Gmail</h3>
              <span className="status-tag status-tag-neutral" style={{ marginLeft: 'auto' }}>Read-Only</span>
            </div>
            <div style={{ fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              Customer Reality
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Extracts subjective claims, requested refund amounts, and context from customer emails without modifying inboxes.
            </p>
          </div>

          {/* Stripe */}
          <div className="panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <div style={{ color: 'var(--text-secondary)' }}><IconStripe size={20} /></div>
              <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text)' }}>Stripe</h3>
              <span className="status-tag status-tag-accent" style={{ marginLeft: 'auto' }}>TEST Mode</span>
            </div>
            <div style={{ fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              Financial Reality
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Authoritative transaction ledger. Validates charge existence, settled statuses, amounts, invoices, and prior refunds.
            </p>
          </div>

          {/* Slack */}
          <div className="panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
              <div style={{ color: 'var(--text-secondary)' }}><IconSlack size={20} /></div>
              <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text)' }}>Slack</h3>
              <span className="status-tag status-tag-neutral" style={{ marginLeft: 'auto' }}>#billing</span>
            </div>
            <div style={{ fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>
              Internal Reality
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              Searches internal conversation history to identify custom contracts, sales agreements, and onboarding fee agreements.
            </p>
          </div>
        </div>
      </section>

      {/* How RECON Works (4 Steps) */}
      <section style={{ marginBottom: '64px' }}>
        <div style={{ marginBottom: '24px' }}>
          <div className="label-caps" style={{ marginBottom: '8px' }}>Investigation Workflow</div>
          <h2 className="heading-lg">How RECON reconciles reality</h2>
        </div>

        <div className="workflow-steps-grid">
          {[
            {
              step: '01',
              title: 'Collect Evidence',
              desc: 'Queries customer emails, Stripe charges, and Slack internal discussions simultaneously.'
            },
            {
              step: '02',
              title: 'Reconcile & Detect',
              desc: 'Cross-checks charge amounts, invoices, and flags contradictions between claims and records.'
            },
            {
              step: '03',
              title: 'Decide & Guard',
              desc: 'AI recommends an action. Deterministic safety engine validates 8 strict safety checks.'
            },
            {
              step: '04',
              title: 'Approve & Verify',
              desc: 'Mandatory human approval gate. Executes in Stripe TEST mode and verifies resulting state.'
            }
          ].map((item) => (
            <div key={item.step} className="panel" style={{ padding: '24px' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: '600', color: 'var(--accent)', marginBottom: '12px' }}>
                {item.step}
              </div>
              <h3 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text)', marginBottom: '8px' }}>
                {item.title}
              </h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Safety By Design Pipeline */}
      <section style={{ marginBottom: '64px' }}>
        <div className="panel" style={{ padding: '32px' }}>
          <div style={{ maxWidth: '680px', marginBottom: '28px' }}>
            <div className="label-caps" style={{ marginBottom: '8px' }}>Security Guarantee</div>
            <h2 className="heading-md" style={{ marginBottom: '10px' }}>
              The LLM never directly executes financial actions.
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Financial operations require deterministic guarantees. The AI model is strictly restricted to returning structured recommendations. Only audited Python backend logic can execute transactions after passing the safety engine and human sign-off.
            </p>
          </div>

          {/* Pipeline flow */}
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '8px',
            padding: '16px',
            background: 'var(--surface-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--line)',
            fontSize: '0.78rem'
          }}>
            <span style={{ fontWeight: '500', color: 'var(--text)' }}>LLM Recommendation</span>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <span style={{ fontWeight: '600', color: 'var(--accent)' }}>Deterministic Safety Engine</span>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <span style={{ fontWeight: '600', color: 'var(--warning)' }}>Human Approval Gate</span>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <span style={{ fontWeight: '600', color: 'var(--text)' }}>Stripe TEST Execution</span>
            <span style={{ color: 'var(--text-muted)' }}>→</span>
            <span style={{ fontWeight: '600', color: 'var(--success)' }}>State Verification</span>
          </div>
        </div>
      </section>

      {/* CTA Box */}
      <section style={{ textAlign: 'center', padding: '40px 24px', background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 'var(--radius-lg)' }}>
        <h2 className="heading-lg" style={{ marginBottom: '12px' }}>
          Investigate a live billing dispute
        </h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '24px', maxWidth: '520px', margin: '0 auto 24px' }}>
          Select a pre-configured test scenario or provide natural language query to inspect real-time multi-app reconciliation.
        </p>
        <button
          className="btn-primary"
          onClick={handleOpen}
          style={{ padding: '12px 28px', fontSize: '0.92rem' }}
        >
          Open Investigation Workspace
          <IconArrowRight size={16} />
        </button>
      </section>

    </div>
  );
}
