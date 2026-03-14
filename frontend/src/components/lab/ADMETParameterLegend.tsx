'use client';

import React from 'react';
import { Info, CheckCircle, AlertTriangle, XCircle, MinusCircle } from 'lucide-react';

export const ADMETParameterLegend = () => {
    return (
        <div className="p-6 rounded-2xl bg-[var(--surface)] border border-[var(--border)] backdrop-blur-md">
            <div className="flex items-center gap-2 mb-4">
                <Info className="w-5 h-5 text-blue-500" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wider">ADMET Parameter Guide</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                    <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase">Key Metrics</h4>
                    <ul className="space-y-2">
                        <li className="text-xs text-[var(--text-primary)]">
                            <span className="font-semibold">HIA:</span> Human Intestinal Absorption (Higher is better)
                        </li>
                        <li className="text-xs text-[var(--text-primary)]">
                            <span className="font-semibold">Caco-2:</span> Intestinal permeability (Higher log cm/s is better)
                        </li>
                        <li className="text-xs text-[var(--text-primary)]">
                            <span className="font-semibold">hERG:</span> Cardiovascular risk liability (Lower is safer)
                        </li>
                        <li className="text-xs text-[var(--text-primary)]">
                            <span className="font-semibold">DILI:</span> Drug-Induced Liver Injury risk (Lower is safer)
                        </li>
                        <li className="text-xs text-[var(--text-primary)]">
                            <span className="font-semibold">QED:</span> Quantitative Estimate of Drug-likeness (Scale 0-1)
                        </li>
                    </ul>
                </div>
                
                <div className="space-y-3">
                    <h4 className="text-xs font-bold text-[var(--text-secondary)] uppercase">Status Indicators</h4>
                    <ul className="space-y-3">
                        <li className="flex items-start gap-2 text-xs text-[var(--text-primary)]">
                            <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                            <span><span className="font-semibold text-green-500">Success:</span> Parameter within favourable pharmacological or safety range.</span>
                        </li>
                        <li className="flex items-start gap-2 text-xs text-[var(--text-primary)]">
                            <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0" />
                            <span><span className="font-semibold text-yellow-500">Warning:</span> Marginal profile; may require structural optimization.</span>
                        </li>
                        <li className="flex items-start gap-2 text-xs text-[var(--text-primary)]">
                            <XCircle className="w-4 h-4 text-red-500 shrink-0" />
                            <span><span className="font-semibold text-red-500">Danger:</span> Non-compliant profile; high toxicological or PK liability.</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    );
};
