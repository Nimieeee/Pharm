'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

/**
 * ErrorBoundary catches unhandled React errors and shows a recovery UI
 * instead of crashing the entire app with a white screen.
 */
class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('[ErrorBoundary] Uncaught error:', error, errorInfo);
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    padding: '2rem',
                    textAlign: 'center',
                    color: 'var(--text-secondary, #888)',
                }}>
                    <h2 style={{ marginBottom: '0.5rem', color: 'var(--text-primary, #fff)' }}>
                        Something went wrong
                    </h2>
                    <p style={{ marginBottom: '1rem', maxWidth: '400px' }}>
                        An unexpected error occurred. Try refreshing the page.
                    </p>
                    <button
                        onClick={this.handleRetry}
                        style={{
                            padding: '0.5rem 1.5rem',
                            borderRadius: '0.5rem',
                            border: '1px solid var(--border, #333)',
                            background: 'var(--card-bg, #1a1a1a)',
                            color: 'var(--text-primary, #fff)',
                            cursor: 'pointer',
                        }}
                    >
                        Try Again
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
