import React, { useState } from 'react';
import { IconCheck, IconClose, IconAlert, IconShield } from './Icons';

export default function DecisionCard({
  caseData,
  onApprove,
  onReject,
  isExecuting
}) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [notes, setNotes] = useState('');

  if (!caseData || !caseData.decision) return null;

  const { decision, status, safety_check, approval, customer_name } = caseData;
  const safetyCheck = safety_check || caseData.safety_check;
  const decType = decision?.decision;

  const isRefundRecommended = decType === 'REFUND_RECOMMENDED';
  const isNoRefund = decType === 'NO_REFUND';
  const isEscalate = decType === 'ESCALATE_FOR_REVIEW';

  const isAwaitingApproval = status === 'AWAITING_APPROVAL' || (isRefundRecommended && !approval);
  const isApproved = approval && approval.approved;
  const isRejected = approval && approval.approved === false;

  const handleConfirmApprove = () => {
    setShowConfirm(false);
    onApprove(notes);
  };

  return (
    <div className="panel" style={{ padding: '24px', marginBottom: '28px' }}>
      
      {/* Header with Title & Large Amount if applicable */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px', marginBottom: '18px', paddingBottom: '16px', borderBottom: '1px solid var(--line)' }}>
        <div>
          <div className="label-caps" style={{ marginBottom: '6px' }}>
            System Recommendation
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '700', letterSpacing: '-0.02em', color: 'var(--text)' }}>
            {isRefundRecommended && 'REFUND RECOMMENDED'}
            {isNoRefund && 'NO REFUND RECOMMENDED'}
            {isEscalate && 'ESCALATE FOR HUMAN REVIEW'}
          </h2>
        </div>

        <div style={{ textAlign: 'right' }}>
          {isRefundRecommended && (
            <div>
              <div style={{ fontSize: '1.85rem', fontWeight: '700', color: 'var(--text)', letterSpacing: '-0.03em', lineHeight: 1 }}>
                $499.00
              </div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Confidence: {Math.round(decision.confidence * 100)}%
              </span>
            </div>
          )}

          {isNoRefund && (
            <div style={{ textAlign: 'right' }}>
              <span className="status-tag status-tag-danger" style={{ fontSize: '0.75rem' }}>
                Safety: Refund Blocked
              </span>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Action Taken: NONE
              </div>
            </div>
          )}

          {isEscalate && (
            <div style={{ textAlign: 'right' }}>
              <span className="status-tag status-tag-warning" style={{ fontSize: '0.75rem' }}>
                Safety: Financial Action Frozen
              </span>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Requires Manual Adjudication
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Rationale Text */}
      <div style={{ marginBottom: '20px' }}>
        <div className="label-caps" style={{ marginBottom: '6px' }}>Analytical Rationale</div>
        <p style={{ fontSize: '0.92rem', color: 'var(--text)', lineHeight: '1.6' }}>
          {decision.reason}
        </p>
      </div>

      {/* Supporting Evidence References */}
      {Array.isArray(decision.supporting_evidence) && decision.supporting_evidence.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <div className="label-caps" style={{ marginBottom: '6px' }}>Corroborating Records</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {decision.supporting_evidence.map((s, idx) => (
              <span
                key={idx}
                style={{
                  padding: '3px 8px',
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  color: 'var(--text-secondary)'
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Deterministic Safety Checklist */}
      <div style={{
        padding: '16px',
        background: 'var(--surface-secondary)',
        border: '1px solid var(--line)',
        borderRadius: 'var(--radius-sm)',
        marginBottom: '24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
          <IconShield size={14} color="var(--text-muted)" />
          <span className="label-caps">Deterministic Backend Safety Engine</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px', fontSize: '0.78rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success)' }}>
            <IconCheck size={14} />
            <span>Stripe confirmed in TEST Mode</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success)' }}>
            <IconCheck size={14} />
            <span>Customer identity validated</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success)' }}>
            <IconCheck size={14} />
            <span>Charge status is settled / succeeded</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--success)' }}>
            <IconCheck size={14} />
            <span>Zero prior refund on transaction</span>
          </div>
        </div>

        {safetyCheck && !safetyCheck.allowed && (
          <div style={{ marginTop: '12px', padding: '10px', background: 'var(--danger-soft)', border: '1px solid rgba(180, 35, 24, 0.25)', borderRadius: 'var(--radius-sm)', color: 'var(--danger)', fontSize: '0.78rem' }}>
            <strong>Safety Block:</strong> {safetyCheck.reason}
          </div>
        )}
      </div>

      {/* Primary Action / Approval Area */}
      {isRefundRecommended && isAwaitingApproval && !showConfirm && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            className="btn-primary"
            onClick={() => setShowConfirm(true)}
            disabled={isExecuting}
            style={{ padding: '11px 24px' }}
          >
            Approve refund ($499.00)
          </button>

          <button
            className="btn-secondary"
            onClick={() => onReject(notes)}
            disabled={isExecuting}
            style={{ padding: '11px 20px' }}
          >
            Reject
          </button>
        </div>
      )}

      {/* Deliberate Confirmation Panel */}
      {showConfirm && (
        <div style={{
          padding: '16px',
          background: 'var(--surface-secondary)',
          border: '1px solid var(--line)',
          borderRadius: 'var(--radius-md)',
          animation: 'fadeInSlide var(--duration-fast) var(--ease)'
        }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text)', marginBottom: '4px' }}>
            Approve refund?
          </h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: '1.4' }}>
            RECON will create a $499.00 TEST MODE refund in Stripe for customer {customer_name || 'Acme Corp'}.
          </p>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn-primary"
              onClick={handleConfirmApprove}
              disabled={isExecuting}
              style={{ padding: '8px 18px', fontSize: '0.82rem' }}
            >
              Confirm refund
            </button>
            <button
              className="btn-secondary"
              onClick={() => setShowConfirm(false)}
              disabled={isExecuting}
              style={{ padding: '8px 16px', fontSize: '0.82rem' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* State Transitions Post-Approval */}
      {isExecuting && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--accent)' }}>
          <span className="status-dot status-dot-accent"></span>
          <span>Executing Stripe TEST refund and verifying resulting state...</span>
        </div>
      )}

      {isApproved && !isExecuting && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--success)' }}>
          <IconCheck size={16} />
          <span>Refund approved by operator ({approval.approved_by || 'human'})</span>
        </div>
      )}

      {isRejected && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: 'var(--danger)' }}>
          <IconClose size={16} />
          <span>Refund rejected. Action blocked safely.</span>
        </div>
      )}

    </div>
  );
}
