import React, { useState } from 'react';
import { IconClock, IconChevronDown } from './Icons';

export default function ToolTrace({ trace = [] }) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (trace.length === 0) return null;

  const getToolDisplayName = (toolName) => {
    if (toolName.includes('gmail')) return 'Gmail';
    if (toolName.includes('stripe_list') || toolName.includes('stripe_charges')) return 'Stripe';
    if (toolName.includes('stripe_create_refund')) return 'Stripe Action';
    if (toolName.includes('stripe_get_refund')) return 'Stripe Verification';
    if (toolName.includes('slack_search')) return 'Slack';
    if (toolName.includes('slack_post')) return 'Slack Notification';
    if (toolName.includes('reconcile')) return 'RECON Reconciliation';
    if (toolName.includes('decision')) return 'RECON Decision';
    if (toolName.includes('safety')) return 'Deterministic Safety';
    if (toolName.includes('approval')) return 'Human Approval';
    return toolName;
  };

  const getToolDescription = (toolName, error) => {
    if (error) return `Error: ${error}`;
    if (toolName.includes('gmail')) return 'Customer complaint retrieved and claims extracted';
    if (toolName.includes('stripe_list')) return 'Settled charges and transaction ledger queried';
    if (toolName.includes('stripe_create_refund')) return 'Stripe TEST refund transaction executed';
    if (toolName.includes('stripe_get_refund')) return 'State verified in Stripe ledger';
    if (toolName.includes('slack_search')) return 'Internal channel context and agreements queried';
    if (toolName.includes('slack_post')) return 'Post-action audit notification dispatched';
    if (toolName.includes('reconcile')) return 'Cross-system evidence cross-referenced for contradictions';
    if (toolName.includes('decision')) return 'Recommendation and confidence generated';
    if (toolName.includes('safety')) return 'Deterministic 8-point safety checks validated';
    if (toolName.includes('approval')) return 'Manual authorization received from operator';
    return 'Operation completed successfully';
  };

  return (
    <div className="panel" style={{ padding: '24px', marginBottom: '28px' }}>
      
      {/* Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          userSelect: 'none',
          paddingBottom: isExpanded ? '16px' : '0',
          borderBottom: isExpanded ? '1px solid var(--line)' : 'none'
        }}
      >
        <div>
          <div className="label-caps" style={{ marginBottom: '4px' }}>Execution Trace</div>
          <h3 className="heading-md">
            Investigation Timeline ({trace.length} Operations)
          </h3>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
          <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
          <div style={{ transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
            <IconChevronDown size={14} />
          </div>
        </div>
      </div>

      {/* Vertical Timeline with Thin Line */}
      {isExpanded && (
        <div style={{ position: 'relative', marginTop: '20px', paddingLeft: '24px' }}>
          
          {/* Subtle vertical connecting rule */}
          <div style={{
            position: 'absolute',
            left: '6px',
            top: '8px',
            bottom: '12px',
            width: '1px',
            background: 'var(--line)'
          }}></div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {trace.map((item, idx) => {
              const stepNum = String(idx + 1).padStart(2, '0');
              const isError = item.status === 'error';

              return (
                <div key={item.id || idx} style={{ position: 'relative', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                  
                  {/* Subtle Node Dot */}
                  <div style={{
                    position: 'absolute',
                    left: '-24px',
                    top: '4px',
                    width: '13px',
                    height: '13px',
                    borderRadius: '50%',
                    background: isError ? 'var(--danger)' : 'var(--surface)',
                    border: `1px solid ${isError ? 'var(--danger)' : 'var(--text-subtle)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: isError ? '#FFFFFF' : 'var(--text-muted)' }}></div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '2px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {stepNum}
                      </span>
                      <strong style={{ fontSize: '0.85rem', color: 'var(--text)' }}>
                        {getToolDisplayName(item.tool)}
                      </strong>
                    </div>

                    <p style={{ fontSize: '0.78rem', color: isError ? 'var(--danger)' : 'var(--text-secondary)' }}>
                      {getToolDescription(item.tool, item.error)}
                    </p>
                  </div>

                  <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {item.duration_ms}ms
                    </span>
                  </div>

                </div>
              );
            })}
          </div>

        </div>
      )}

    </div>
  );
}
