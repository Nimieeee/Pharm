'use client';

import React from 'react';
import { CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';

export type StatusType = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

interface StatusBadgeProps {
  status: StatusType;
  label: string;
  className?: string;
}

const statusConfig = {
  success: {
    icon: CheckCircle,
    bg: 'bg-green-500/10',
    text: 'text-green-500',
    border: 'border-green-500/20'
  },
  warning: {
    icon: AlertCircle,
    bg: 'bg-amber-500/10',
    text: 'text-amber-500',
    border: 'border-amber-500/20'
  },
  danger: {
    icon: AlertTriangle,
    bg: 'bg-red-500/10',
    text: 'text-red-500',
    border: 'border-red-500/20'
  },
  info: {
    icon: Info,
    bg: 'bg-blue-500/10',
    text: 'text-blue-500',
    border: 'border-blue-500/20'
  },
  neutral: {
    icon: Info,
    bg: 'bg-slate-500/10',
    text: 'text-slate-500',
    border: 'border-slate-500/20'
  }
};

export default function StatusBadge({ status, label, className = '' }: StatusBadgeProps) {
  const config = statusConfig[status] || statusConfig.neutral;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${config.bg} ${config.text} ${config.border} ${className}`}>
      <Icon className="w-3.5 h-3.5" />
      {label}
    </span>
  );
}
