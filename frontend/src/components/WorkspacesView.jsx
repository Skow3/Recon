import React, { useState, useEffect } from 'react';
import InvestigationBar from './InvestigationBar';
import EvidenceMatrix from './EvidenceMatrix';
import ReconciliationCard from './ReconciliationCard';
import DecisionCard from './DecisionCard';
import ActionVerifiedCard from './ActionVerifiedCard';
import ToolTrace from './ToolTrace';
import WorkspaceDropdown from './WorkspaceDropdown';
import {
  IconFolder,
  IconBriefcase,
  IconMail,
  IconStripe,
  IconSlack,
  IconShield,
  IconCheck,
  IconAlert,
  IconArrowRight,
  IconPlus,
  IconClose,
  IconClock,
  IconTrash
} from './Icons';

export default function WorkspacesView({
  // Props for Finance Operations investigation
  userRequest,
  setUserRequest,
  customerName,
  setCustomerName,
  customerEmail,
  setCustomerEmail,
  selectedScenarioId,
  handleSelectScenario,
  handleSelectCustomLive,
  handleClearScenario,
  runInvestigationFlow,
  isInvestigating,
  currentCase,
  trace,
  handleApprove,
  handleReject,
  isExecuting,
  setCurrentCase,
  setNotification
}) {
  const [selectedWorkspace, setSelectedWorkspace] = useState('ws_finance');
  const [workspaces, setWorkspaces] = useState([]);
  const [loadingWorkspaces, setLoadingWorkspaces] = useState(false);

  // Deletion State
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeletingWs, setIsDeletingWs] = useState(false);

  // Internship Monitor State
  const [internFilter, setInternFilter] = useState('subject:(interview OR offer OR application)');
  const [targetChannel, setTargetChannel] = useState('internship');
  const [isRunningInternship, setIsRunningInternship] = useState(false);
  const [internshipResult, setInternshipResult] = useState(null);

  // New Workspace Modal State
  const [showNewModal, setShowNewModal] = useState(false);
  const [modalStep, setModalStep] = useState(1); // 1: Define Goal, 2: Requirements & Channel
  const [newWsName, setNewWsName] = useState('');
  const [newWsGoal, setNewWsGoal] = useState('');
  const [newWsSlackChannel, setNewWsSlackChannel] = useState('general');
  const [isPlanning, setIsPlanning] = useState(false);
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const [isCreatingWs, setIsCreatingWs] = useState(false);

  // Custom Workspace Execution State
  const [customWorkflow, setCustomWorkflow] = useState(null);
  const [customTriggerQuery, setCustomTriggerQuery] = useState('');
  const [customChannel, setCustomChannel] = useState('general');
  const [isRunningCustom, setIsRunningCustom] = useState(false);
  const [customRunResult, setCustomRunResult] = useState(null);

  // Load custom workspace details when selected
  useEffect(() => {
    setShowDeleteConfirm(false);
    if (selectedWorkspace !== 'ws_finance' && selectedWorkspace !== 'ws_internships') {
      fetch(`/api/workspaces/${selectedWorkspace}`)
        .then(res => res.json())
        .then(data => {
          if (data.workflows && data.workflows.length > 0) {
            setCustomWorkflow(data.workflows[0]);
            setCustomTriggerQuery(data.workflows[0].trigger?.filter || data.description || data.workflows[0].goal || '');
            if (data.workflows[0].configuration?.target_channel) {
              setCustomChannel(data.workflows[0].configuration.target_channel);
            }
          }
        })
        .catch(err => console.error('Failed to load custom workspace details:', err));
    }
  }, [selectedWorkspace]);

  // Execute custom workspace agent
  const handleRunCustom = async (forceReprocess = false) => {
    if (!customWorkflow) return;
    try {
      setIsRunningCustom(true);
      setCustomRunResult(null);

      const res = await fetch(`/api/workflows/${customWorkflow.id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          force_reprocess: forceReprocess,
          target_channel: customChannel,
          search_query: customTriggerQuery || customWorkflow.goal
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Execution failed');
      }

      const result = await res.json();
      setCustomRunResult(result);

      if (result.status === 'SKIPPED_DUPLICATE') {
        setNotification({
          type: 'warning',
          message: 'Deduplication engine active: Event already processed. Duplicate execution suppressed.'
        });
      } else if (result.status === 'NO_MATCHING_EMAILS') {
        setNotification({
          type: 'warning',
          message: result.reason || 'Inbox scanned: 0 messages matched the query in your Gmail inbox.'
        });
      } else {
        setNotification({
          type: 'success',
          message: `Live agent workflow '${customWorkflow.name}' ingested '${result.trigger_event?.subject || 'email'}' and dispatched to #${customChannel}.`
        });
      }
    } catch (err) {
      setNotification({ type: 'error', message: `Execution failed: ${err.message}` });
    } finally {
      setIsRunningCustom(false);
    }
  };

  // Load workspaces list from backend
  const loadWorkspaces = async () => {
    try {
      setLoadingWorkspaces(true);
      const res = await fetch('/api/workspaces');
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data.workspaces || []);
      }
    } catch (err) {
      console.error('Failed to load workspaces:', err);
    } finally {
      setLoadingWorkspaces(false);
    }
  };

  useEffect(() => {
    loadWorkspaces();
  }, []);

  // Run internship scan
  const handleRunInternship = async (forceReprocess = false) => {
    try {
      setIsRunningInternship(true);
      setInternshipResult(null);

      const res = await fetch('/api/workflows/wf_internship_monitor/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          search_query: internFilter,
          force_reprocess: forceReprocess,
          target_channel: targetChannel
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Execution failed');
      }

      const result = await res.json();
      setInternshipResult(result);

      if (result.status === 'SKIPPED_DUPLICATE') {
        setNotification({
          type: 'warning',
          message: 'Deduplication engine active: This email was already processed. Notification safely suppressed.'
        });
      } else if (result.status === 'NO_MATCHING_EMAILS') {
        setNotification({
          type: 'warning',
          message: result.reason || 'Inbox scanned: 0 recruiter emails found matching filter in your Gmail account.'
        });
      } else if (result.extracted_data?.importance === 'LOW') {
        setNotification({
          type: 'warning',
          message: 'Noise suppression policy: Marketing newsletter filtered. Slack alert suppressed.'
        });
      } else {
        setNotification({
          type: 'success',
          message: `Recruiter update processed: ${result.extracted_data?.company || 'Candidate'} alert delivered to #${targetChannel}.`
        });
      }
    } catch (err) {
      setNotification({ type: 'error', message: `Execution failed: ${err.message}` });
    } finally {
      setIsRunningInternship(false);
    }
  };

  // Delete custom workspace
  const handleDeleteWorkspace = async (wsId) => {
    if (!wsId || wsId === 'ws_finance' || wsId === 'ws_internships') return;
    try {
      setIsDeletingWs(true);
      const res = await fetch(`/api/workspaces/${wsId}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to delete workspace');
      }
      setNotification({ type: 'success', message: 'Workspace deleted successfully.' });
      setSelectedWorkspace('ws_finance');
      setShowDeleteConfirm(false);
      await loadWorkspaces();
    } catch (err) {
      setNotification({ type: 'error', message: `Delete failed: ${err.message}` });
    } finally {
      setIsDeletingWs(false);
    }
  };

  // Analyze Goal & Requirements
  const handleAnalyzeGoal = async () => {
    if (!newWsGoal.trim()) return;
    try {
      setIsPlanning(true);
      const res = await fetch('/api/workflows/interpret-goal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal: newWsGoal
        })
      });
      if (!res.ok) throw new Error('Requirement analysis failed');
      const plan = await res.json();
      setGeneratedPlan(plan);
      setNewWsName(plan.workflow_name || 'Custom Agent Workspace');
      if (plan.suggested_channel) {
        setNewWsSlackChannel(plan.suggested_channel);
      }
      setModalStep(2);
    } catch (err) {
      setNotification({ type: 'error', message: `Analysis error: ${err.message}` });
    } finally {
      setIsPlanning(false);
    }
  };

  // Submit New Workspace Creation
  const handleCreateWorkspace = async () => {
    if (!newWsName.trim()) return;
    try {
      setIsCreatingWs(true);
      const apps = generatedPlan?.recommended_apps || ['gmail', 'slack'];
      const res = await fetch('/api/workspaces', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newWsName,
          description: newWsGoal,
          connected_apps: apps,
          agent_instructions: `Execute workflow for: ${newWsGoal}`,
          permissions: generatedPlan?.required_permissions || {},
          plan: generatedPlan || null,
          workflow_name: generatedPlan?.workflow_name || newWsName,
          target_channel: newWsSlackChannel || 'general'
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to create workspace');
      }
      const created = await res.json();

      await loadWorkspaces();
      setSelectedWorkspace(created.id);
      setShowNewModal(false);
      setModalStep(1);
      setNewWsName('');
      setNewWsGoal('');
      setGeneratedPlan(null);
      setNotification({ type: 'success', message: `Workspace '${created.name}' created with active workflow.` });
    } catch (err) {
      setNotification({ type: 'error', message: `Creation failed: ${err.message}` });
    } finally {
      setIsCreatingWs(false);
    }
  };

  const activeWsData = workspaces.find(w => w.id === selectedWorkspace) || {
    id: selectedWorkspace,
    name: selectedWorkspace === 'ws_finance' ? 'Finance Operations' : 'Internship Applications',
    connected_apps: selectedWorkspace === 'ws_finance' ? ['gmail', 'stripe', 'slack'] : ['gmail', 'slack'],
    description: selectedWorkspace === 'ws_finance'
      ? 'Enterprise billing dispute investigation, cross-system reconciliation across Stripe & Gmail, and gated refund execution.'
      : 'Recruiter inbox monitoring, interview schedule and offer letter extraction, noise filtering, and structured Slack delivery.'
  };

  return (
    <div>
      {/* Workspace Selector Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        marginBottom: '24px',
        paddingBottom: '16px',
        borderBottom: '1px solid var(--line)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{
            fontSize: '0.74rem',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: 'var(--text-muted)'
          }}>
            Workspace
          </span>
          <WorkspaceDropdown
            workspaces={workspaces}
            selectedWorkspace={selectedWorkspace}
            onSelectWorkspace={setSelectedWorkspace}
            onNewWorkspace={() => setShowNewModal(true)}
          />
        </div>

        <button
          onClick={() => setShowNewModal(true)}
          className="btn-secondary"
          style={{ fontSize: '0.8rem', padding: '7px 14px' }}
        >
          <IconPlus size={14} />
          New Workspace
        </button>
      </div>

      {/* Workspace Header Panel */}
      <div className="panel" style={{ padding: '20px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <h2 className="heading-md" style={{ margin: 0 }}>
                {activeWsData.name}
              </h2>
              <span className="status-tag status-tag-success" style={{ fontSize: '0.72rem' }}>
                Active Workspace
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {activeWsData.id}
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, maxWidth: '640px' }}>
              {activeWsData.description}
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'flex-end' }}>
            {/* Security & Boundary Matrix */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              background: 'var(--surface-secondary)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px 16px',
              minWidth: '260px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                <span style={{ fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Connected Apps
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>
                  {activeWsData.connected_apps?.join(', ').toUpperCase()}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.72rem' }}>
                <span style={{ fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  Security Boundary
                </span>
                <span style={{ color: activeWsData.connected_apps?.includes('stripe') ? 'var(--accent)' : 'var(--success)', fontWeight: '600' }}>
                  {activeWsData.connected_apps?.includes('stripe') ? 'Gated Approval (Stripe)' : 'Strict Isolation (Non-Financial)'}
                </span>
              </div>
            </div>

            {/* Delete Workspace Action for custom workspaces */}
            {activeWsData.id !== 'ws_finance' && activeWsData.id !== 'ws_internships' && (
              <div>
                {showDeleteConfirm ? (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 12px',
                    background: 'var(--surface-secondary)',
                    border: '1px solid var(--danger)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.78rem'
                  }}>
                    <span style={{ color: 'var(--danger)', fontWeight: '500' }}>Delete workspace?</span>
                    <button
                      onClick={() => handleDeleteWorkspace(activeWsData.id)}
                      disabled={isDeletingWs}
                      style={{
                        background: 'var(--danger)',
                        color: '#fff',
                        border: 'none',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.74rem',
                        cursor: 'pointer',
                        fontWeight: '600'
                      }}
                    >
                      {isDeletingWs ? 'Deleting...' : 'Confirm'}
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      disabled={isDeletingWs}
                      style={{
                        background: 'transparent',
                        color: 'var(--text-muted)',
                        border: '1px solid var(--line)',
                        padding: '3px 8px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.74rem',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: 'transparent',
                      border: '1px solid var(--line)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '5px 10px',
                      fontSize: '0.75rem',
                      color: 'var(--danger)',
                      cursor: 'pointer'
                    }}
                  >
                    <IconTrash size={13} color="var(--danger)" />
                    Delete Workspace
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* WORKSPACE 1: FINANCE OPERATIONS (EXACT BILLING INVESTIGATION INTERFACE) */}
      {selectedWorkspace === 'ws_finance' && (
        <div>
          {/* Investigation Query Bar with Editable Inputs */}
          <InvestigationBar
            userRequest={userRequest}
            setUserRequest={setUserRequest}
            customerName={customerName}
            setCustomerName={setCustomerName}
            customerEmail={customerEmail}
            setCustomerEmail={setCustomerEmail}
            selectedScenarioId={selectedScenarioId}
            onClearScenario={handleClearScenario}
            onInvestigate={() => runInvestigationFlow(userRequest, customerName, customerEmail, selectedScenarioId)}
            isInvestigating={isInvestigating}
            caseStatus={currentCase?.status}
          />

          {/* Two-Column Investigation Experience */}
          {currentCase ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
              {/* Left Column: Evidence & Reconciliation */}
              <div>
                <EvidenceMatrix evidence={currentCase.evidence} />
                <ReconciliationCard reconciliation={currentCase.reconciliation} />
                <ToolTrace trace={trace} />
              </div>

              {/* Right Column: Case Summary, Decision, Approval & Verification */}
              <div>
                <DecisionCard
                  caseData={currentCase}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  isExecuting={isExecuting}
                />
                <ActionVerifiedCard
                  action={currentCase.action}
                  verification={currentCase.verification}
                  customerName={currentCase.customer_name}
                />
              </div>
            </div>
          ) : (
            <div className="panel" style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '0.92rem', color: 'var(--text)', fontWeight: '600', marginBottom: '6px' }}>
                Finance Workspace: No Active Billing Investigation
              </div>
              <p style={{ fontSize: '0.82rem', maxWidth: '440px', margin: '0 auto 20px' }}>
                Enter the customer's name, email, and dispute details in the investigation bar above to reconcile records across Stripe and Gmail.
              </p>
              <button
                className="btn-primary"
                onClick={() => runInvestigationFlow(userRequest, customerName, customerEmail, null)}
              >
                Investigate & Reconcile
              </button>
            </div>
          )}
        </div>
      )}

      {/* WORKSPACE 2: INTERNSHIP APPLICATIONS MONITOR */}
      {selectedWorkspace === 'ws_internships' && (
        <div>
          {/* Operational Control Bar */}
          <div className="panel" style={{ padding: '20px 24px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="status-dot status-dot-accent"></span>
                <span className="label-caps" style={{ margin: 0 }}>
                  Recruiter Inbox Scanner & Alert Gateway
                </span>
              </div>
              <span className="status-tag status-tag-neutral" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                TRIGGER: GMAIL
              </span>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
                Recruiter Inbox Search Query / Filter
              </label>
              <input
                type="text"
                value={internFilter}
                onChange={e => setInternFilter(e.target.value)}
                placeholder="e.g. subject:(interview OR offer OR application)"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--line)',
                  background: 'var(--surface-secondary)',
                  color: 'var(--text)',
                  fontSize: '0.85rem',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '500' }}>Destination:</span>
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '5px 10px',
                  fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)'
                }}>
                  <IconSlack size={13} />
                  <span>#{targetChannel}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn-secondary"
                  onClick={() => handleRunInternship(false)}
                  disabled={isRunningInternship}
                  style={{ fontSize: '0.82rem' }}
                >
                  Test Deduplication
                </button>
                <button
                  className="btn-primary"
                  onClick={() => handleRunInternship(true)}
                  disabled={isRunningInternship}
                  style={{ fontSize: '0.82rem' }}
                >
                  {isRunningInternship ? 'Scanning Inbox...' : 'Scan Recruiter Inbox'}
                </button>
              </div>
            </div>
          </div>

          {/* Internship Execution Results */}
          {internshipResult ? (
            <div>
              {/* Two Column Dossier */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
                {/* Left Column: Extracted Intelligence */}
                <div>
                  <div className="panel" style={{ padding: '24px', marginBottom: '24px' }}>
                    <div className="label-caps" style={{ marginBottom: '8px' }}>Entity Extraction & Relevance</div>
                    <h3 className="heading-md" style={{ marginBottom: '16px' }}>
                      {internshipResult.extracted_data?.company || 'Recruiter Communication'}
                    </h3>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Role Position</span>
                        <span style={{ fontWeight: '600', color: 'var(--text)' }}>{internshipResult.extracted_data?.role}</span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Update Classification</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '600', color: 'var(--text)' }}>
                          {internshipResult.extracted_data?.update_type}
                        </span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Priority Level</span>
                        <span className={`status-tag ${internshipResult.extracted_data?.importance === 'HIGH' ? 'status-tag-danger' : internshipResult.extracted_data?.importance === 'MEDIUM' ? 'status-tag-accent' : 'status-tag-neutral'}`}>
                          {internshipResult.extracted_data?.importance}
                        </span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Action Required</span>
                        <span style={{ fontWeight: '600', color: internshipResult.extracted_data?.action_required ? 'var(--danger)' : 'var(--text-muted)' }}>
                          {internshipResult.extracted_data?.action_required ? 'YES — Candidate Action Needed' : 'NO — Informational Only'}
                        </span>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Action Deadline</span>
                        <span style={{ fontWeight: '600', color: internshipResult.extracted_data?.deadline ? 'var(--accent)' : 'var(--text-muted)' }}>
                          {internshipResult.extracted_data?.deadline || 'No hard deadline stated'}
                        </span>
                      </div>

                      <div style={{ paddingTop: '8px' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                          Summary Assessment
                        </span>
                        <p style={{ fontSize: '0.84rem', color: 'var(--text)', lineHeight: '1.5', margin: 0 }}>
                          {internshipResult.extracted_data?.summary}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column: Slack Delivery & Verification */}
                <div>
                  {/* Slack Notification Preview */}
                  <div className="panel" style={{ padding: '24px', marginBottom: '24px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                      <div className="label-caps">Slack Delivery Preview</div>
                      <span className="status-tag status-tag-neutral">#{targetChannel}</span>
                    </div>

                    {internshipResult.action_result?.status === 'SUPPRESSED' ? (
                      <div style={{
                        padding: '16px',
                        background: 'var(--surface-secondary)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--line)',
                        color: 'var(--text-muted)',
                        fontSize: '0.82rem'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text)', marginBottom: '4px' }}>
                          <IconShield size={15} color="var(--warning)" />
                          <strong style={{ fontSize: '0.85rem' }}>Notification Suppressed by Noise Policy</strong>
                        </div>
                        {internshipResult.action_result?.reason}
                      </div>
                    ) : (
                      <div style={{
                        background: 'var(--surface-secondary)',
                        border: '1px solid var(--line)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '16px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                          <div style={{
                            width: '24px',
                            height: '24px',
                            borderRadius: '4px',
                            background: 'var(--accent)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#fff',
                            fontSize: '0.7rem',
                            fontWeight: '700'
                          }}>
                            R
                          </div>
                          <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text)' }}>RECON Bot</span>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>APP • Just now</span>
                        </div>

                        <div style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.78rem',
                          lineHeight: '1.6',
                          color: 'var(--text)',
                          whiteSpace: 'pre-wrap'
                        }}>
                          {internshipResult.action_result?.message?.text || 'Notification payload dispatched.'}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Verification Card */}
                  <div className="panel" style={{ padding: '24px' }}>
                    <div className="label-caps" style={{ marginBottom: '8px' }}>Action Verification</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                      <span className={`status-dot ${internshipResult.verification_result?.verified ? 'status-dot-success' : 'status-dot-warning'}`}></span>
                      <h4 style={{ fontSize: '0.92rem', fontWeight: '600', margin: 0, color: 'var(--text)' }}>
                        {internshipResult.verification_result?.verified ? 'Delivery Verified by Multi-App Gateway' : 'Action Blocked'}
                      </h4>
                    </div>

                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
                      Event ID: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{internshipResult.message_id}</code>.
                      Logged to SQLite ProcessedEvents and immutable audit trail.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="panel" style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '0.92rem', color: 'var(--text)', fontWeight: '600', marginBottom: '6px' }}>
                Internship Applications Agent Ready
              </div>
              <p style={{ fontSize: '0.82rem', maxWidth: '440px', margin: '0 auto 20px' }}>
                RECON is connected to Gmail and Slack. Click below to scan unread recruiter correspondence and post structured alerts.
              </p>
              <button
                className="btn-primary"
                onClick={() => handleRunInternship(true)}
              >
                Scan Recruiter Inbox
              </button>
            </div>
          )}
        </div>
      )}

      {/* CUSTOM WORKSPACES VIEW */}
      {selectedWorkspace !== 'ws_finance' && selectedWorkspace !== 'ws_internships' && (
        <div>
          {/* Active Workflow Header & Trigger Bar */}
          <div className="panel" style={{ padding: '20px 24px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="status-dot status-dot-accent"></span>
                <span className="label-caps" style={{ margin: 0 }}>
                  Active Workflow: {customWorkflow ? customWorkflow.name : `${activeWsData.name} Orchestrator`}
                </span>
              </div>
              <span className="status-tag status-tag-neutral" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                TRIGGER: {(customWorkflow?.trigger?.app || activeWsData.connected_apps?.[0] || 'GMAIL').toUpperCase()}
              </span>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '6px' }}>
                Operational Query / Email Search Filter
              </label>
              <input
                type="text"
                value={customTriggerQuery}
                onChange={e => setCustomTriggerQuery(e.target.value)}
                placeholder="e.g. check for emails regarding groceries or upcoming shopping list"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--line)',
                  background: 'var(--surface-secondary)',
                  color: 'var(--text)',
                  fontSize: '0.85rem',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '500' }}>Destination:</span>
                <div style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '5px 10px',
                  fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)'
                }}>
                  <IconSlack size={13} />
                  <span>#{customChannel}</span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn-secondary"
                  onClick={() => handleRunCustom(false)}
                  disabled={isRunningCustom || !customWorkflow}
                  style={{ fontSize: '0.82rem' }}
                >
                  Test Deduplication
                </button>
                <button
                  className="btn-primary"
                  onClick={() => handleRunCustom(true)}
                  disabled={isRunningCustom || !customWorkflow}
                  style={{ fontSize: '0.82rem' }}
                >
                  {isRunningCustom ? 'Checking Email & Executing...' : 'Check Email & Run Agent'}
                </button>
              </div>
            </div>
          </div>

          {/* Execution Results Dossier */}
          {customRunResult ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', alignItems: 'flex-start' }}>
              {/* Left Column: Extracted Intelligence */}
              <div>
                <div className="panel" style={{ padding: '24px', marginBottom: '24px' }}>
                  <div className="label-caps" style={{ marginBottom: '8px' }}>Ingested Event & Extracted Context</div>
                  <h3 className="heading-md" style={{ marginBottom: '16px' }}>
                    {customRunResult.trigger_event?.subject || activeWsData.name}
                  </h3>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Source Subsystem</span>
                      <span style={{ fontWeight: '600', color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                        {customRunResult.trigger_event?.source?.toUpperCase() || 'GMAIL'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Target Subsystems</span>
                      <span style={{ fontWeight: '600', color: 'var(--text)', fontFamily: 'var(--font-mono)' }}>
                        {activeWsData.connected_apps?.join(', ').toUpperCase()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Policy Validation</span>
                      <span className="status-tag status-tag-success">
                        PASSED (Non-Financial Isolation)
                      </span>
                    </div>

                    {customRunResult.trigger_event?.sender && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Sender</span>
                        <span style={{ fontWeight: '500', color: 'var(--text)', fontSize: '0.8rem' }}>
                          {customRunResult.trigger_event.sender}
                        </span>
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: '8px', fontSize: '0.84rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Event ID</span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text)' }}>
                        {customRunResult.message_id}
                      </span>
                    </div>

                    <div style={{ paddingTop: '8px' }}>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                        Intelligence Briefing
                      </span>
                      <p style={{ fontSize: '0.84rem', color: 'var(--text)', lineHeight: '1.5', margin: 0 }}>
                        {customRunResult.extracted_data?.summary || 'Agent evaluated trigger event and verified non-financial security boundaries.'}
                      </p>
                    </div>

                    {customRunResult.trigger_event?.body && (
                      <div style={{ paddingTop: '8px', borderTop: '1px solid var(--line)' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                          Extracted Email Body
                        </span>
                        <div style={{
                          fontSize: '0.8rem',
                          fontFamily: 'var(--font-mono)',
                          color: 'var(--text)',
                          background: 'var(--surface-secondary)',
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          whiteSpace: 'pre-wrap',
                          maxHeight: '120px',
                          overflowY: 'auto'
                        }}>
                          {customRunResult.trigger_event.body}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: Slack Delivery & Verification */}
              <div>
                <div className="panel" style={{ padding: '24px', marginBottom: '24px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                    <div className="label-caps">Slack Delivery Preview</div>
                    <span className="status-tag status-tag-neutral">#{customChannel}</span>
                  </div>

                  <div style={{
                    background: 'var(--surface-secondary)',
                    border: '1px solid var(--line)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '16px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                      <div style={{
                        width: '24px',
                        height: '24px',
                        borderRadius: '4px',
                        background: 'var(--accent)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        fontSize: '0.7rem',
                        fontWeight: '700'
                      }}>
                        R
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text)' }}>RECON Bot</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>APP • Just now</span>
                    </div>

                    <div style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.78rem',
                      lineHeight: '1.6',
                      color: 'var(--text)',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {customRunResult.action_result?.message?.text || 'Dispatched structured agent notification to destination channel.'}
                    </div>
                  </div>
                </div>

                {/* Verification Card */}
                <div className="panel" style={{ padding: '24px' }}>
                  <div className="label-caps" style={{ marginBottom: '8px' }}>Action Verification</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                    <span className={`status-dot ${customRunResult.verification_result?.verified ? 'status-dot-success' : 'status-dot-warning'}`}></span>
                    <h4 style={{ fontSize: '0.92rem', fontWeight: '600', margin: 0, color: 'var(--text)' }}>
                      {customRunResult.verification_result?.verified ? 'Delivery Verified by Multi-App Gateway' : 'Action Blocked'}
                    </h4>
                  </div>

                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
                    Event ID: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{customRunResult.message_id}</code>.
                    Logged to SQLite ProcessedEvents and immutable audit trail.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="panel" style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: '0.92rem', color: 'var(--text)', fontWeight: '600', marginBottom: '6px' }}>
                Workspace Agent Ready: {activeWsData.name}
              </div>
              <p style={{ fontSize: '0.82rem', maxWidth: '440px', margin: '0 auto 20px' }}>
                Click "Run Agent Workflow" above to ingest trigger events, check deduplication, and dispatch verified updates to Slack.
              </p>
              <button
                className="btn-primary"
                onClick={() => handleRunCustom(true)}
                disabled={isRunningCustom || !customWorkflow}
              >
                Execute Agent Workflow
              </button>
            </div>
          )}
        </div>
      )}

      {/* NEW WORKSPACE MODAL */}
      {showNewModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '20px'
        }}>
          <div className="panel" style={{ width: '100%', maxWidth: '600px', maxHeight: '90vh', overflowY: 'auto', padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <h3 className="heading-md" style={{ margin: 0 }}>
                  {modalStep === 1 ? 'Create New Agent Workspace' : 'Workspace Requirements & Setup'}
                </h3>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {modalStep === 1 ? 'Define your operational goal in natural language' : 'Requirements identified for your operational goal'}
                </span>
              </div>
              <button
                onClick={() => {
                  setShowNewModal(false);
                  setModalStep(1);
                }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              >
                <IconClose size={18} />
              </button>
            </div>

            {/* STEP 1: GOAL INTENT INPUT */}
            {modalStep === 1 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Operational Goal / Intent
                  </label>
                  <textarea
                    value={newWsGoal}
                    onChange={e => setNewWsGoal(e.target.value)}
                    placeholder="e.g. Check my email for an upcoming list of groceries to buy and notify me"
                    rows={4}
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--line)',
                      background: 'var(--surface-secondary)',
                      color: 'var(--text)',
                      fontSize: '0.85rem',
                      fontFamily: 'inherit',
                      resize: 'vertical'
                    }}
                  />
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)', display: 'block', marginTop: '4px' }}>
                    Type what you want RECON to monitor, reconcile, or automate across your connected services.
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                  <button
                    className="btn-secondary"
                    onClick={() => setShowNewModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="btn-primary"
                    onClick={handleAnalyzeGoal}
                    disabled={isPlanning || !newWsGoal.trim()}
                  >
                    {isPlanning ? 'Analyzing Requirements...' : 'Analyze Requirements'}
                  </button>
                </div>
              </div>
            )}

            {/* STEP 2: REQUIREMENTS ANALYSIS & CONFIGURATION */}
            {modalStep === 2 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {/* Analyzed Intent Summary */}
                <div style={{
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--surface-secondary)',
                  border: '1px solid var(--line)',
                  fontSize: '0.82rem'
                }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', display: 'block', marginBottom: '2px' }}>
                    Analyzed Goal
                  </span>
                  <span style={{ color: 'var(--text)' }}>"{newWsGoal}"</span>
                </div>

                {/* Requirements / Connected Apps */}
                <div>
                  <div className="label-caps" style={{ marginBottom: '8px' }}>Required Connected Apps</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                    {(generatedPlan?.recommended_apps || ['gmail', 'slack']).map(app => {
                      const isGmail = app === 'gmail';
                      const isSlack = app === 'slack';
                      const isStripe = app === 'stripe';
                      return (
                        <div
                          key={app}
                          style={{
                            padding: '12px 14px',
                            borderRadius: 'var(--radius-sm)',
                            border: '1px solid var(--line)',
                            background: 'var(--surface-secondary)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px'
                          }}
                        >
                          {isGmail && <IconMail size={18} color="var(--accent)" />}
                          {isSlack && <IconSlack size={18} color="var(--accent)" />}
                          {isStripe && <IconStripe size={18} color="var(--accent)" />}
                          {!isGmail && !isSlack && !isStripe && <IconFolder size={18} />}

                          <div>
                            <div style={{ fontSize: '0.84rem', fontWeight: '600', color: 'var(--text)' }}>
                              {app.toUpperCase()}
                            </div>
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                              {isGmail ? 'Read & Ingest Emails' : isSlack ? 'Channel Alerts' : isStripe ? 'Reconcile Charges' : 'Connected App'}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Slack Channel & Reminder if Slack is needed */}
                {(generatedPlan?.recommended_apps || []).includes('slack') && (
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '6px' }}>
                      Slack Destination Channel
                    </label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.85rem' }}>#</span>
                      <input
                        type="text"
                        value={newWsSlackChannel}
                        onChange={e => setNewWsSlackChannel(e.target.value.replace(/^#/, ''))}
                        placeholder="general"
                        style={{
                          flex: 1,
                          padding: '8px 12px',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--line)',
                          background: 'var(--surface-secondary)',
                          color: 'var(--text)',
                          fontSize: '0.85rem'
                        }}
                      />
                    </div>

                    {/* Slack Invitation Reminder Callout */}
                    <div style={{
                      padding: '12px 14px',
                      background: 'var(--surface-secondary)',
                      border: '1px solid var(--line)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px'
                    }}>
                      <IconSlack size={16} color="var(--accent)" style={{ marginTop: '2px', flexShrink: 0 }} />
                      <div>
                        <strong style={{ color: 'var(--text)', display: 'block', marginBottom: '2px' }}>Slack Bot Invitation Reminder</strong>
                        Remember to invite the RECON bot to <code>#{newWsSlackChannel || 'general'}</code> in your Slack workspace (e.g. <code>/invite @RECON Bot</code>) so alerts can be posted.
                      </div>
                    </div>
                  </div>
                )}

                {/* Workspace Name Input */}
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: '600', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Workspace Display Name
                  </label>
                  <input
                    type="text"
                    value={newWsName}
                    onChange={e => setNewWsName(e.target.value)}
                    placeholder="e.g. Grocery List Notifier"
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--line)',
                      background: 'var(--surface-secondary)',
                      color: 'var(--text)',
                      fontSize: '0.85rem'
                    }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                  <button
                    className="btn-secondary"
                    onClick={() => setModalStep(1)}
                  >
                    Back to Goal
                  </button>
                  <button
                    className="btn-primary"
                    onClick={handleCreateWorkspace}
                    disabled={isCreatingWs || !newWsName.trim()}
                  >
                    {isCreatingWs ? 'Creating Workspace...' : 'Create Workspace & Workflow'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
