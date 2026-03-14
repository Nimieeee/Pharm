'use client';

import React from 'react';
import AuthGuard from '@/components/shared/AuthGuard';
import CreationStudio from '@/components/studio/CreationStudio';

export default function StudioPage() {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <CreationStudio />
      </div>
    </AuthGuard>
  );
}
