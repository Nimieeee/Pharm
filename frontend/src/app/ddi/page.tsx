'use client';

import AuthGuard from '@/components/shared/AuthGuard';
import DDIDashboard from '@/components/ddi/DDIDashboard';

export default function DDIPage() {
  return (
    <AuthGuard>
      <DDIDashboard />
    </AuthGuard>
  );
}
