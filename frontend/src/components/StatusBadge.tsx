import React from 'react';
import { Badge } from '@/components/ui/badge';

interface StatusBadgeProps {
  status: 'up' | 'down' | 'warning';
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variants = {
    up: { variant: 'success' as const, label: 'Up' },
    down: { variant: 'destructive' as const, label: 'Down' },
    warning: { variant: 'warning' as const, label: 'Warning' },
  };

  const config = variants[status];

  return <Badge variant={config.variant}>{config.label}</Badge>;
}

export function StatusDot({ status }: StatusBadgeProps) {
  const colors = {
    up: 'bg-green-500',
    down: 'bg-red-500',
    warning: 'bg-yellow-500',
  };

  return (
    <span className={`inline-block w-2 h-2 rounded-full ${colors[status]}`} />
  );
}
