import React, { useState, useRef, useEffect } from 'react';
import {
  IconStripe,
  IconBriefcase,
  IconFolder,
  IconChevronDown,
  IconCheck,
  IconPlus,
  IconSearch,
  IconClose
} from './Icons';

/**
 * WorkspaceDropdown
 * Modular dropdown component replacing horizontal workspace tiles.
 * Provides instant switching between Core Workspaces and Custom Agent Workspaces,
 * inline search/filtering, and quick creation action.
 */
export default function WorkspaceDropdown({
  workspaces = [],
  selectedWorkspace = 'ws_finance',
  onSelectWorkspace,
  onNewWorkspace
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Close dropdown on Escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  // Find currently active workspace metadata
  const activeWs = workspaces.find(w => w.id === selectedWorkspace) || {
    id: selectedWorkspace,
    name: selectedWorkspace === 'ws_finance'
      ? 'Finance Operations'
      : selectedWorkspace === 'ws_internships'
      ? 'Internship Applications'
      : 'Custom Workspace',
    connected_apps: selectedWorkspace === 'ws_finance'
      ? ['gmail', 'stripe', 'slack']
      : ['gmail', 'slack']
  };

  const getWorkspaceIcon = (id, size = 15) => {
    if (id === 'ws_finance') return <IconStripe size={size} />;
    if (id === 'ws_internships') return <IconBriefcase size={size} />;
    return <IconFolder size={size} />;
  };

  // Flagship Core Workspaces
  const coreWorkspaces = [
    {
      id: 'ws_finance',
      name: 'Finance Operations',
      subtitle: 'Stripe, Gmail, Slack',
      appsCount: 3,
      tag: 'Approval Gate'
    },
    {
      id: 'ws_internships',
      name: 'Internship Applications',
      subtitle: 'Gmail, Slack',
      appsCount: 2,
      tag: 'Inbox Monitor'
    }
  ];

  // User-created Custom Workspaces
  const customWorkspaces = workspaces.filter(
    w => w.id !== 'ws_finance' && w.id !== 'ws_internships'
  );

  // Search filter predicate
  const query = searchQuery.trim().toLowerCase();
  const filterMatches = (name, sub = '') => {
    if (!query) return true;
    return name.toLowerCase().includes(query) || sub.toLowerCase().includes(query);
  };

  const filteredCore = coreWorkspaces.filter(
    w => filterMatches(w.name, w.subtitle)
  );

  const filteredCustom = customWorkspaces.filter(
    w => filterMatches(w.name, (w.connected_apps || []).join(' '))
  );

  const handleSelect = (id) => {
    if (onSelectWorkspace) {
      onSelectWorkspace(id);
    }
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleCreateNew = () => {
    setIsOpen(false);
    setSearchQuery('');
    if (onNewWorkspace) {
      onNewWorkspace();
    }
  };

  const appsCount = activeWs.connected_apps?.length || (activeWs.id === 'ws_finance' ? 3 : 2);

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          padding: '7px 14px',
          background: isOpen ? 'var(--surface-secondary)' : 'var(--surface)',
          border: `1px solid ${isOpen ? 'var(--text)' : 'var(--line)'}`,
          borderRadius: 'var(--radius-sm)',
          color: 'var(--text)',
          cursor: 'pointer',
          fontSize: '0.84rem',
          fontWeight: '500',
          transition: 'all var(--duration-fast) var(--ease)',
          boxShadow: isOpen ? '0 0 0 1px var(--text)' : 'none',
          outline: 'none'
        }}
        title="Switch active workspace"
      >
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '22px',
          height: '22px',
          borderRadius: '4px',
          background: 'var(--surface-secondary)',
          color: 'var(--text-secondary)'
        }}>
          {getWorkspaceIcon(activeWs.id, 14)}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: '600', color: 'var(--text)' }}>
            {activeWs.name}
          </span>
          <span
            className={`status-tag ${activeWs.id === 'ws_finance' ? 'status-tag-accent' : 'status-tag-neutral'}`}
            style={{ fontSize: '0.68rem', padding: '1px 6px' }}
          >
            {appsCount} Apps
          </span>
        </div>

        <IconChevronDown
          size={13}
          color="var(--text-muted)"
          style={{
            transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform var(--duration-fast) var(--ease)',
            marginLeft: '4px'
          }}
        />
      </button>

      {/* Modular Popover Dropdown */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            width: '330px',
            background: 'var(--surface)',
            border: '1px solid var(--line)',
            borderRadius: 'var(--radius-md)',
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.14), 0 2px 8px rgba(0, 0, 0, 0.06)',
            zIndex: 100,
            overflow: 'hidden'
          }}
        >
          {/* Header & Search */}
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'var(--surface-secondary)',
              border: '1px solid var(--line)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 10px'
            }}>
              <IconSearch size={13} color="var(--text-muted)" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search workspaces..."
                autoFocus
                style={{
                  border: 'none',
                  background: 'transparent',
                  outline: 'none',
                  fontSize: '0.78rem',
                  color: 'var(--text)',
                  width: '100%',
                  fontFamily: 'inherit'
                }}
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  <IconClose size={12} />
                </button>
              )}
            </div>
          </div>

          {/* Workspaces Scrollable List */}
          <div style={{ maxHeight: '320px', overflowY: 'auto', padding: '6px' }}>
            {/* Core Workspaces Section */}
            {filteredCore.length > 0 && (
              <div>
                <div style={{
                  fontSize: '0.66rem',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: 'var(--text-muted)',
                  padding: '6px 8px 4px'
                }}>
                  Core Workspaces
                </div>

                {filteredCore.map((ws) => {
                  const isSelected = selectedWorkspace === ws.id;
                  return (
                    <button
                      key={ws.id}
                      type="button"
                      onClick={() => handleSelect(ws.id)}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'var(--surface-secondary)' : 'transparent',
                        border: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'background var(--duration-fast) var(--ease)',
                        marginBottom: '2px'
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.background = 'var(--surface-secondary)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '24px',
                          height: '24px',
                          borderRadius: '4px',
                          background: 'var(--surface)',
                          border: '1px solid var(--line)',
                          color: 'var(--text-secondary)',
                          flexShrink: 0
                        }}>
                          {getWorkspaceIcon(ws.id, 14)}
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div style={{
                            fontSize: '0.82rem',
                            fontWeight: isSelected ? '600' : '500',
                            color: 'var(--text)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}>
                            {ws.name}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {ws.subtitle}
                          </div>
                        </div>
                      </div>

                      {isSelected && (
                        <div style={{ color: 'var(--accent)', marginLeft: '8px', flexShrink: 0 }}>
                          <IconCheck size={14} />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            {/* Custom Workspaces Section */}
            {filteredCustom.length > 0 && (
              <div style={{ marginTop: filteredCore.length > 0 ? '6px' : 0 }}>
                <div style={{
                  fontSize: '0.66rem',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: 'var(--text-muted)',
                  padding: '6px 8px 4px',
                  borderTop: filteredCore.length > 0 ? '1px solid var(--line)' : 'none',
                  marginTop: filteredCore.length > 0 ? '4px' : 0
                }}>
                  Custom Workspaces ({customWorkspaces.length})
                </div>

                {filteredCustom.map((ws) => {
                  const isSelected = selectedWorkspace === ws.id;
                  const appsList = ws.connected_apps && ws.connected_apps.length > 0
                    ? ws.connected_apps.map(a => a.charAt(0).toUpperCase() + a.slice(1)).join(', ')
                    : 'Custom Agent';

                  return (
                    <button
                      key={ws.id}
                      type="button"
                      onClick={() => handleSelect(ws.id)}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 10px',
                        borderRadius: 'var(--radius-sm)',
                        background: isSelected ? 'var(--surface-secondary)' : 'transparent',
                        border: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'background var(--duration-fast) var(--ease)',
                        marginBottom: '2px'
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) e.currentTarget.style.background = 'var(--surface-secondary)';
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) e.currentTarget.style.background = 'transparent';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '24px',
                          height: '24px',
                          borderRadius: '4px',
                          background: 'var(--surface)',
                          border: '1px solid var(--line)',
                          color: 'var(--text-secondary)',
                          flexShrink: 0
                        }}>
                          <IconFolder size={14} />
                        </div>
                        <div style={{ minWidth: 0 }}>
                          <div style={{
                            fontSize: '0.82rem',
                            fontWeight: isSelected ? '600' : '500',
                            color: 'var(--text)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                          }}>
                            {ws.name}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {appsList} • {ws.connected_apps?.length || 0} Apps
                          </div>
                        </div>
                      </div>

                      {isSelected && (
                        <div style={{ color: 'var(--accent)', marginLeft: '8px', flexShrink: 0 }}>
                          <IconCheck size={14} />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            {filteredCore.length === 0 && filteredCustom.length === 0 && (
              <div style={{ padding: '20px 8px', textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                No workspaces match "{searchQuery}"
              </div>
            )}
          </div>

          {/* Action Footer */}
          <div style={{
            padding: '8px',
            borderTop: '1px solid var(--line)',
            background: 'var(--surface-secondary)'
          }}>
            <button
              type="button"
              onClick={handleCreateNew}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '7px 10px',
                borderRadius: 'var(--radius-sm)',
                background: 'transparent',
                border: 'none',
                color: 'var(--text)',
                fontSize: '0.8rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'background var(--duration-fast) var(--ease)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--surface)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
              }}
            >
              <IconPlus size={14} color="var(--accent)" />
              <span>Create New Workspace</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
