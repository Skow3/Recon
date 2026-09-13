import React, { useState, useEffect } from 'react';
import TopNav from './components/TopNav';
import LandingHero from './components/LandingHero';
import WorkspacesView from './components/WorkspacesView';
import AppsView from './components/AppsView';
import ScenarioSelector from './components/ScenarioSelector';
import InvestigationBar from './components/InvestigationBar';
import EvidenceMatrix from './components/EvidenceMatrix';
import ReconciliationCard from './components/ReconciliationCard';
import DecisionCard from './components/DecisionCard';
import ActionVerifiedCard from './components/ActionVerifiedCard';
import ToolTrace from './components/ToolTrace';
import EvaluationTab from './components/EvaluationTab';
import AuditTab from './components/AuditTab';
import { IconClose } from './components/Icons';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="panel" style={{ padding: '32px', marginBottom: '24px', border: '1px solid var(--danger)' }}>
          <h3 className="heading-md" style={{ color: 'var(--danger)', marginBottom: '8px' }}>
            Rendering Notice
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred.'}
          </p>
          <button
            className="btn-secondary"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              if (this.props.onReset) this.props.onReset();
            }}
          >
            Reset Workspace
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [health, setHealth] = useState(null);

  // Theme Management (Default: LIGHT, respects localStorage)
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('recon-theme');
    if (saved) return saved;
    return 'light'; // Light mode is default first-class
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
    }
    localStorage.setItem('recon-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  // Dispute form state (Defaults to user's live dispute parameters)
  const [userRequest, setUserRequest] = useState("Investigate billing dispute for shiv230102037@iiitmanipur.ac.in regarding duplicate $499 charge");
  const [customerName, setCustomerName] = useState('Shivendra');
  const [customerEmail, setCustomerEmail] = useState('shiv230102037@iiitmanipur.ac.in');
  const [selectedScenarioId, setSelectedScenarioId] = useState(null); // null means 100% Live Mode

  // Active investigation state
  const [currentCase, setCurrentCase] = useState(null);
  const [trace, setTrace] = useState([]);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [notification, setNotification] = useState(null);

  // Fetch health check on mount
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => console.error('Health check failed:', err));
  }, []);

  const handleClearScenario = () => {
    setSelectedScenarioId(null);
  };

  const handleSelectCustomLive = () => {
    setSelectedScenarioId(null);
    setCustomerName('Shivendra');
    setCustomerEmail('shiv230102037@iiitmanipur.ac.in');
    setUserRequest('Investigate billing dispute for shiv230102037@iiitmanipur.ac.in regarding duplicate $499 charge');
    setNotification({ type: 'success', message: 'Switched to 100% Live Mode. Real Gmail inbox, Stripe ledger, and Slack will be queried.' });
  };

  const handleSelectScenario = async (sc) => {
    setSelectedScenarioId(sc.id);
    setUserRequest(sc.query);
    setCustomerName(sc.customer);
    setCustomerEmail(sc.email);

    // Auto-run investigation on scenario selection
    await runInvestigationFlow(sc.query, sc.customer, sc.email, sc.id);
  };

  const runInvestigationFlow = async (query, custName, custEmail, scId) => {
    setIsInvestigating(true);
    setCurrentCase(null);
    setTrace([]);
    setNotification(null);

    try {
      // 1. Create Case
      const createRes = await fetch('/api/cases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_request: query || userRequest,
          customer_name: custName || customerName,
          customer_email: custEmail || customerEmail,
          scenario_id: scId || selectedScenarioId
        })
      });
      if (!createRes.ok) {
        const errJson = await createRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `Failed to create case (${createRes.status})`);
      }
      const caseData = await createRes.json();
      setCurrentCase(caseData);

      // 2. Start Investigation
      const invRes = await fetch(`/api/cases/${caseData.id}/investigate`, {
        method: 'POST'
      });
      if (!invRes.ok) {
        const errJson = await invRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `Investigation failed (${invRes.status})`);
      }
      const invData = await invRes.json();
      setCurrentCase(invData);

      // 3. Fetch tool trace
      const traceRes = await fetch(`/api/cases/${caseData.id}/trace`);
      if (traceRes.ok) {
        const traceData = await traceRes.json();
        setTrace(Array.isArray(traceData) ? traceData : []);
      }

    } catch (err) {
      setNotification({ type: 'error', message: `Investigation failed: ${err.message}` });
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleApprove = async (notes) => {
    if (!currentCase) return;
    setIsExecuting(true);
    try {
      // Record human approval
      const appRes = await fetch(`/api/cases/${currentCase.id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approved: true,
          approved_by: 'human',
          notes: notes || 'Operator approved refund after cross-referencing Stripe and Slack'
        })
      });
      if (!appRes.ok) {
        const errJson = await appRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `Approval failed (${appRes.status})`);
      }
      const appData = await appRes.json();
      setCurrentCase(appData);

      // Trigger backend execution + deterministic safety check + verification
      const execRes = await fetch(`/api/cases/${currentCase.id}/execute`, {
        method: 'POST'
      });
      if (!execRes.ok) {
        const errJson = await execRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `Execution blocked by safety engine (${execRes.status})`);
      }
      const execData = await execRes.json();
      setCurrentCase(execData);

      // Refresh trace
      const traceRes = await fetch(`/api/cases/${currentCase.id}/trace`);
      if (traceRes.ok) {
        const traceData = await traceRes.json();
        setTrace(Array.isArray(traceData) ? traceData : []);
      }

      setNotification({ type: 'success', message: 'Stripe refund executed and verified in ledger. Slack audit alert posted.' });
    } catch (err) {
      setNotification({ type: 'error', message: `Execution failed: ${err.message}` });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleReject = async (notes) => {
    if (!currentCase) return;
    try {
      const rejRes = await fetch(`/api/cases/${currentCase.id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notes: notes || 'Rejected by operator in workspace'
        })
      });
      if (!rejRes.ok) {
        const errJson = await rejRes.json().catch(() => ({}));
        throw new Error(errJson.detail || `Rejection failed (${rejRes.status})`);
      }
      const rejData = await rejRes.json();
      setCurrentCase(rejData);

      // Refresh trace
      const traceRes = await fetch(`/api/cases/${currentCase.id}/trace`);
      if (traceRes.ok) {
        const traceData = await traceRes.json();
        setTrace(Array.isArray(traceData) ? traceData : []);
      }

      setNotification({ type: 'warning', message: 'Refund was rejected. Action blocked safely.' });
    } catch (err) {
      setNotification({ type: 'error', message: `Rejection failed: ${err.message}` });
    }
  };

  return (
    <div className="editorial-bg" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Top Navigation */}
      <TopNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        theme={theme}
        toggleTheme={toggleTheme}
        health={health}
      />

      {/* Main View Area */}
      <main className="container" style={{ flex: 1, padding: '36px 24px 80px' }}>
        
        {/* Clean Notification Toast */}
        {notification && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '24px',
            fontSize: '0.82rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: notification.type === 'error' ? 'var(--danger-soft)' : notification.type === 'warning' ? 'var(--warning-soft)' : 'var(--success-soft)',
            border: `1px solid ${notification.type === 'error' ? 'rgba(180, 35, 24, 0.3)' : notification.type === 'warning' ? 'rgba(154, 103, 0, 0.3)' : 'rgba(24, 121, 78, 0.3)'}`,
            color: notification.type === 'error' ? 'var(--danger)' : notification.type === 'warning' ? 'var(--warning)' : 'var(--success)'
          }}>
            <span>{notification.message}</span>
            <button
              onClick={() => setNotification(null)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
            >
              <IconClose size={14} />
            </button>
          </div>
        )}

        <ErrorBoundary onReset={() => { setActiveTab('overview'); setCurrentCase(null); }}>
          {/* 1. OVERVIEW / PRODUCT LANDING */}
          {activeTab === 'overview' && (
            <LandingHero
              onOpenWorkspaces={() => setActiveTab('workspaces')}
              onStartInvestigation={() => setActiveTab('workspaces')}
              onOpenApps={() => setActiveTab('apps')}
              onViewEvaluation={() => setActiveTab('evaluation')}
            />
          )}

          {/* 2. MULTI-APP WORKSPACES (Finance & Internship Flagships + Custom Workspaces) */}
          {(activeTab === 'workspaces' || activeTab === 'investigate') && (
            <WorkspacesView
              userRequest={userRequest}
              setUserRequest={setUserRequest}
              customerName={customerName}
              setCustomerName={setCustomerName}
              customerEmail={customerEmail}
              setCustomerEmail={setCustomerEmail}
              selectedScenarioId={selectedScenarioId}
              handleSelectScenario={handleSelectScenario}
              handleSelectCustomLive={handleSelectCustomLive}
              handleClearScenario={handleClearScenario}
              runInvestigationFlow={runInvestigationFlow}
              isInvestigating={isInvestigating}
              currentCase={currentCase}
              trace={trace}
              handleApprove={handleApprove}
              handleReject={handleReject}
              isExecuting={isExecuting}
              setCurrentCase={setCurrentCase}
              setNotification={setNotification}
            />
          )}

          {/* 3. APPS CONNECTION CENTER */}
          {activeTab === 'apps' && (
            <AppsView setNotification={setNotification} />
          )}

          {/* 4. RELIABILITY BENCHMARKS */}
          {activeTab === 'evaluation' && <EvaluationTab />}

          {/* 5. AUDIT TRAIL */}
          {activeTab === 'audit' && <AuditTab currentCaseId={currentCase?.id} />}
        </ErrorBoundary>

      </main>

      {/* Understated Footer */}
      <footer style={{ borderTop: '1px solid var(--line)', padding: '24px 0', background: 'var(--surface)' }}>
        <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <div>
            <strong style={{ color: 'var(--text)' }}>RECON</strong> — Multi-app AI agent for financial operations.
          </div>
          <div>
            "Don't automate the action before verifying reality."
          </div>
        </div>
      </footer>

    </div>
  );
}
