import React, { useState, useEffect } from 'react';
import { IconSearch } from './Icons';

export default function InvestigationBar({
  userRequest,
  setUserRequest,
  customerName,
  setCustomerName,
  customerEmail,
  setCustomerEmail,
  selectedScenarioId,
  onClearScenario,
  onInvestigate,
  isInvestigating,
  caseStatus
}) {
  const [loadingStep, setLoadingStep] = useState(0);

  const steps = [
    'Connecting to Gmail API & extracting customer claims...',
    'Querying Stripe TEST ledger & charges...',
    'Analyzing Slack #billing internal context...',
    'Reconciling cross-system evidence & evaluating safety...'
  ];

  useEffect(() => {
    let interval;
    if (isInvestigating) {
      setLoadingStep(0);
      interval = setInterval(() => {
        setLoadingStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
      }, 700);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [isInvestigating]);

  const handleInputChange = (setter) => (e) => {
    setter(e.target.value);
    if (selectedScenarioId && onClearScenario) {
      onClearScenario();
    }
  };

  return (
    <div className="panel" style={{ padding: '24px', marginBottom: '28px' }}>
      
      {/* Header with Mode Badge and Live Switch */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px', marginBottom: '18px', paddingBottom: '14px', borderBottom: '1px solid var(--line)' }}>
        <div>
          <div className="label-caps" style={{ marginBottom: '2px' }}>Investigation Parameters</div>
          <h3 className="heading-md" style={{ fontSize: '1.05rem' }}>Target Account & Query</h3>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {selectedScenarioId ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="status-tag status-tag-accent" style={{ fontSize: '0.72rem' }}>
                Preset Demo Case
              </span>
              <button
                type="button"
                className="btn-secondary"
                onClick={onClearScenario}
                style={{ padding: '4px 10px', fontSize: '0.72rem', borderRadius: 'var(--radius-sm)' }}
              >
                Switch to Custom Live
              </button>
            </div>
          ) : (
            <span className="status-tag status-tag-success" style={{ fontSize: '0.72rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span className="status-dot status-dot-success" style={{ width: '6px', height: '6px' }}></span>
              100% Live Mode (Real Inbox & Ledger)
            </span>
          )}

          {caseStatus && (
            <span className={`status-tag ${
              caseStatus === 'COMPLETED' ? 'status-tag-success' :
              caseStatus === 'BLOCKED' ? 'status-tag-danger' :
              caseStatus === 'ESCALATED' ? 'status-tag-warning' :
              'status-tag-accent'
            }`}>
              {caseStatus.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>

      {/* Two-Column Customer Target Inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '18px' }}>
        <div>
          <label className="label-caps" style={{ display: 'block', marginBottom: '6px' }}>
            Customer / Account Name
          </label>
          <input
            type="text"
            className="input-editorial"
            value={customerName || ''}
            onChange={handleInputChange(setCustomerName)}
            placeholder="e.g. Shivendra or Acme Corp"
            disabled={isInvestigating}
            style={{ fontSize: '0.88rem', padding: '10px 14px' }}
          />
        </div>

        <div>
          <label className="label-caps" style={{ display: 'block', marginBottom: '6px' }}>
            Customer Email / Identifier
          </label>
          <input
            type="email"
            className="input-editorial"
            value={customerEmail || ''}
            onChange={handleInputChange(setCustomerEmail)}
            placeholder="e.g. shiv230102037@iiitmanipur.ac.in"
            disabled={isInvestigating}
            style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem', padding: '10px 14px' }}
          />
        </div>
      </div>

      {/* Main Investigation Query Input & Investigate Button */}
      <div style={{ marginBottom: '12px' }}>
        <label className="label-caps" style={{ display: 'block', marginBottom: '6px' }}>
          Investigation Query / Complaint Summary
        </label>
        
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <input
              type="text"
              className="input-editorial"
              value={userRequest || ''}
              onChange={handleInputChange(setUserRequest)}
              placeholder="What should RECON investigate? (e.g. Investigate duplicate $499 annual subscription charge for Shivendra)"
              disabled={isInvestigating}
              onKeyDown={(e) => { if (e.key === 'Enter' && !isInvestigating) onInvestigate(); }}
              style={{ fontSize: '0.9rem', padding: '11px 16px' }}
            />
          </div>

          <button
            className="btn-primary"
            onClick={onInvestigate}
            disabled={isInvestigating || !userRequest?.trim() || !customerEmail?.trim()}
            style={{ padding: '11px 24px', fontSize: '0.88rem', whiteSpace: 'nowrap' }}
          >
            <IconSearch size={16} />
            {isInvestigating ? 'Investigating...' : 'Investigate'}
          </button>
        </div>
      </div>

      {/* Meaningful progressive agent activity indicator */}
      {isInvestigating && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'var(--surface-secondary)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span className="status-dot status-dot-accent"></span>
          <span style={{ fontFamily: 'var(--font-mono)' }}>
            {steps[loadingStep]}
          </span>
        </div>
      )}

    </div>
  );
}
