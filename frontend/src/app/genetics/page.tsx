'use client';

import React from 'react';
import AuthGuard from '@/components/shared/AuthGuard';
import GeneticsDashboard from '@/components/genetics/GeneticsDashboard';

export default function GeneticsPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <GeneticsDashboard />
      </div>
    </AuthGuard>
  );
}
