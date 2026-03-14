'use client';

import AuthGuard from '@/components/shared/AuthGuard';
import LiteratureDashboard from '@/components/literature/LiteratureDashboard';

export default function LiteraturePage() {
  return (
    <AuthGuard>
      <LiteratureDashboard />
    </AuthGuard>
  );
}
