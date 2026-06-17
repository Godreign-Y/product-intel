import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'sienna' | 'bush';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  className = '',
}) => (
  <span className={`badge badge-${variant} ${className}`}>{children}</span>
);

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
}

export const Toggle: React.FC<ToggleProps> = ({ checked, onChange, label, description }) => (
  <label className="toggle-row">
    <div className="toggle-info">
      {label && <span className="toggle-label">{label}</span>}
      {description && <span className="toggle-desc">{description}</span>}
    </div>
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={`toggle ${checked ? 'toggle-on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="toggle-thumb" />
    </button>
  </label>
);
