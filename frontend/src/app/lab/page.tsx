'use client';

import React from 'react';
import AuthGuard from '@/components/shared/AuthGuard';
import LabDashboard from '@/components/lab/LabDashboard';

export default function LabPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <LabDashboard />
      </div>
    </AuthGuard>
  );
}
