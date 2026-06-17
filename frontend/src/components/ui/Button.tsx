import React from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'accent' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon,
  loading,
  children,
  className = '',
  disabled,
  ...props
}) => (
  <button
    className={`btn btn-${variant} btn-${size} ${className}`}
    disabled={disabled || loading}
    {...props}
  >
    {loading ? <span className="btn-spinner" /> : icon}
    {children && <span>{children}</span>}
  </button>
);
