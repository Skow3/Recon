import React, { useState } from 'react';
import { ReconLogo, IconSun, IconMoon, IconChevronDown, IconMail, IconStripe, IconSlack } from './Icons';

export default function TopNav({
  activeTab,
  setActiveTab,
  theme,
  toggleTheme,
  health
}) {
  const [showStatusMenu, setShowStatusMenu] = useState(false);
  const isMock = health?.is_mock ?? true;
  const integrations = health?.integrations || {};

  return (
    <nav style={{
      position: 'sticky',
      top: 0,
      zIndex: 50,
      background: 'var(--surface)',
      borderBottom: '1px solid var(--line)',
      backdropFilter: 'blur(8px)',
      transition: 'background-color var(--duration-base) var(--ease), border-color var(--duration-base) var(--ease)'
    }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
        
        {/* Left: Brand & Tagline */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            onClick={() => setActiveTab('overview')}
            style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', userSelect: 'none' }}
          >
            <div style={{
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text)'
            }}>
              <ReconLogo size={22} />
            </div>
            <span style={{ fontSize: '1rem', fontWeight: '700', letterSpacing: '-0.02em', color: 'var(--text)' }}>
              RECON
            </span>
          </div>

          <div style={{ width: '1px', height: '14px', background: 'var(--line)' }}></div>

          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'none', mdDisplay: 'inline' }} className="hidden md:inline">
            Connect your apps. Define what matters. Let your agent handle the rest.
          </span>
        </div>

        {/* Center: Understated Navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'workspaces', label: 'Workspaces' },
            { id: 'apps', label: 'Apps' },
            { id: 'evaluation', label: 'Reliability' },
            { id: 'audit', label: 'Audit Log' }
          ].map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  background: isActive ? 'var(--surface-secondary)' : 'transparent',
                  color: isActive ? 'var(--text)' : 'var(--text-muted)',
                  border: '1px solid',
                  borderColor: isActive ? 'var(--line)' : 'transparent',
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.82rem',
                  fontWeight: isActive ? '600' : '400',
                  cursor: 'pointer',
                  transition: 'all var(--duration-fast) var(--ease)',
                  outline: 'none'
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Right: Systems, Environment & Theme */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          
          {/* Systems Status Dropdown Button */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowStatusMenu(!showStatusMenu)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--surface-secondary)',
                border: '1px solid var(--line)',
                padding: '5px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                outline: 'none'
              }}
              title="System Connectivity Status"
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span className="status-dot status-dot-success"></span>
                <span className="status-dot status-dot-accent"></span>
                <span className="status-dot status-dot-success"></span>
              </div>
              <span style={{ fontWeight: '500' }}>3 Systems</span>
              <IconChevronDown size={12} color="var(--text-muted)" />
            </button>

            {/* Systems Dropdown Popover */}
            {showStatusMenu && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '100%',
                  marginTop: '6px',
                  width: '260px',
                  background: 'var(--surface)',
                  border: '1px solid var(--line)',
                  borderRadius: 'var(--radius-md)',
                  padding: '12px',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.08)',
                  zIndex: 100
                }}
              >
                <div style={{ fontSize: '0.68rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)', marginBottom: '10px' }}>
                  Connected Subsystems
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.78rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <IconMail size={15} color="var(--text-muted)" />
                      <span style={{ fontWeight: '500', color: 'var(--text)' }}>Gmail</span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--success)', fontWeight: '600' }}>Read-Only OAuth</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <IconStripe size={15} color="var(--text-muted)" />
                      <span style={{ fontWeight: '500', color: 'var(--text)' }}>Stripe</span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--accent)', fontWeight: '600' }}>TEST Mode</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', background: 'var(--surface-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <IconSlack size={15} color="var(--text-muted)" />
                      <span style={{ fontWeight: '500', color: 'var(--text)' }}>Slack</span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--success)', fontWeight: '600' }}>#billing</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Environment Indicator (Understated) */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.72rem',
            padding: '4px 8px',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--surface-secondary)',
            color: 'var(--text-secondary)'
          }}>
            <span className={`status-dot ${isMock ? 'status-dot-warning' : 'status-dot-accent'}`}></span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              {isMock ? 'Mock' : 'Live'}
            </span>
          </div>

          {/* Theme Toggle (Monochrome SVG Slider) */}
          <button
            onClick={toggleTheme}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--surface-secondary)',
              border: '1px solid var(--line)',
              color: 'var(--text)',
              cursor: 'pointer',
              outline: 'none',
              transition: 'all var(--duration-fast) var(--ease)'
            }}
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
            aria-label="Toggle Theme"
          >
            {theme === 'light' ? <IconMoon size={15} /> : <IconSun size={15} />}
          </button>
        </div>
      </div>
    </nav>
  );
}
