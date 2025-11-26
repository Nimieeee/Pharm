'use client';

import { Suspense } from 'react';
import { Loader2 } from 'lucide-react';
import DataWorkbench from '@/components/workbench/DataWorkbench';

export default function WorkbenchPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
        <Loader2 size={32} className="text-indigo-500 animate-spin" />
      </div>
    }>
      <DataWorkbench />
    </Suspense>
  );
}
