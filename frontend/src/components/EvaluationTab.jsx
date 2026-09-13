import React, { useState, useEffect } from 'react';
import { IconCheck, IconClose } from './Icons';

export default function EvaluationTab() {
  const [report, setReport] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  const fetchOrRunEvaluation = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const res = await fetch('/api/evaluate', { method: 'POST' });
      if (!res.ok) throw new Error(`Evaluation failed with status ${res.status}`);
      const data = await res.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    fetchOrRunEvaluation();
  }, []);

  return (
    <div style={{ maxWidth: '1040px', margin: '0 auto' }}>
      
      {/* Editorial Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '40px', paddingBottom: '24px', borderBottom: '1px solid var(--line)' }}>
        <div>
          <div className="label-caps" style={{ marginBottom: '6px' }}>Deterministic Benchmark</div>
          <h1 className="heading-lg" style={{ marginBottom: '6px' }}>
            Does RECON know when NOT to act?
          </h1>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
            Audited test suite executing 10 real-world adversarial and edge-case dispute scenarios.
          </p>
        </div>

        <button
          className="btn-primary"
          onClick={fetchOrRunEvaluation}
          disabled={isRunning}
          style={{ padding: '10px 20px', fontSize: '0.85rem' }}
        >
          {isRunning ? 'Running 10 Scenarios...' : 'Run Benchmark'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '14px', background: 'var(--danger-soft)', border: '1px solid rgba(180, 35, 24, 0.25)', borderRadius: 'var(--radius-sm)', color: 'var(--danger)', marginBottom: '24px', fontSize: '0.85rem' }}>
          Error running benchmark: {error}
        </div>
      )}

      {/* Large Typography Numerical Hierarchy (NO GIANT COLORED CARDS) */}
      {report && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '24px', marginBottom: '48px', paddingBottom: '32px', borderBottom: '1px solid var(--line)' }}>
            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: '700', letterSpacing: '-0.03em', lineHeight: 1, color: 'var(--text)', marginBottom: '6px' }}>
                {report.total_cases}
              </div>
              <div className="label-caps">Test Cases</div>
            </div>

            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: '700', letterSpacing: '-0.03em', lineHeight: 1, color: 'var(--text)', marginBottom: '6px' }}>
                {report.decision_accuracy_pct}%
              </div>
              <div className="label-caps">Decision Accuracy</div>
            </div>

            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: '700', letterSpacing: '-0.03em', lineHeight: 1, color: 'var(--text)', marginBottom: '6px' }}>
                {report.unsafe_action_count}
              </div>
              <div className="label-caps">Unsafe Actions</div>
            </div>

            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: '700', letterSpacing: '-0.03em', lineHeight: 1, color: 'var(--text)', marginBottom: '6px' }}>
                {report.false_refund_rate_pct}%
              </div>
              <div className="label-caps">False Refunds</div>
            </div>

            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: '700', letterSpacing: '-0.03em', lineHeight: 1, color: 'var(--text)', marginBottom: '6px' }}>
                {report.duplicate_refund_count}
              </div>
              <div className="label-caps">Duplicate Refunds</div>
            </div>

            <div>
              <div style={{ fontSize: '2.5rem', fontWeight: '700', letterSpacing: '-0.03em', lineHeight: 1, color: 'var(--text)', marginBottom: '6px' }}>
                {report.verification_success_rate_pct}%
              </div>
              <div className="label-caps">Verification Rate</div>
            </div>
          </div>

          {/* Test Suite Table */}
          <div className="panel" style={{ padding: '24px' }}>
            <div style={{ marginBottom: '16px' }}>
              <div className="label-caps" style={{ marginBottom: '4px' }}>Test Suite Results</div>
              <h3 className="heading-md">Individual Scenario Audits</h3>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--line)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px 12px', fontWeight: '500' }}>Case</th>
                    <th style={{ padding: '10px 12px', fontWeight: '500' }}>Expected</th>
                    <th style={{ padding: '10px 12px', fontWeight: '500' }}>Actual</th>
                    <th style={{ padding: '10px 12px', fontWeight: '500' }}>Action Taken</th>
                    <th style={{ padding: '10px 12px', fontWeight: '500' }}>State</th>
                    <th style={{ padding: '10px 12px', fontWeight: '500', textAlign: 'right' }}>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {report.results.map((r, idx) => {
                    const isPass = r.decision_correct && !r.unsafe_action && !r.duplicate_action;
                    return (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--line-subtle)' }}>
                        <td style={{ padding: '12px', fontWeight: '500', color: 'var(--text)' }}>
                          {r.case_name}
                        </td>
                        <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {r.expected_decision.replace(/_/g, ' ')}
                        </td>
                        <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text)' }}>
                          {r.actual_decision.replace(/_/g, ' ')}
                        </td>
                        <td style={{ padding: '12px', color: 'var(--text-secondary)' }}>
                          {r.refund_succeeded ? 'Stripe refund executed' : 'None'}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span className={`status-tag ${
                            r.final_state === 'COMPLETED' ? 'status-tag-success' :
                            r.final_state === 'BLOCKED' ? 'status-tag-danger' :
                            'status-tag-warning'
                          }`} style={{ fontSize: '0.68rem' }}>
                            {r.final_state}
                          </span>
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          <span style={{
                            fontFamily: 'var(--font-mono)',
                            fontWeight: '600',
                            fontSize: '0.75rem',
                            color: isPass ? 'var(--success)' : 'var(--danger)'
                          }}>
                            {isPass ? 'PASS' : 'FAIL'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

    </div>
  );
}
