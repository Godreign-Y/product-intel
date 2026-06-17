import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  variant?: 'default' | 'elevated' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  style,
  variant = 'default',
  padding = 'md',
  interactive = false,
  onClick,
}) => {
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag
      className={`card card-${variant} card-pad-${padding} ${interactive ? 'card-interactive' : ''} ${className}`}
      style={style}
      onClick={onClick}
    >
      {children}
    </Tag>
  );
};

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({ title, subtitle, icon, action }) => (
  <div className="card-header">
    <div className="card-header-text">
      {icon && <span className="card-header-icon">{icon}</span>}
      <div>
        <h3 className="card-title">{title}</h3>
        {subtitle && <p className="card-subtitle">{subtitle}</p>}
      </div>
    </div>
    {action && <div className="card-header-action">{action}</div>}
  </div>
);
