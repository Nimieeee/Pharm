-- Migration 015: Create research_tasks table for background execution
-- This table enables scaling deep research to multiple concurrent users

CREATE TABLE IF NOT EXISTS public.research_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE SET NULL,
    research_question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED
    result_report TEXT,
    error_detail TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

-- Index for worker polling
CREATE INDEX IF NOT EXISTS idx_research_tasks_status ON public.research_tasks(status) WHERE status = 'PENDING';
CREATE INDEX IF NOT EXISTS idx_research_tasks_user_id ON public.research_tasks(user_id);

-- Add comment for documentation
COMMENT ON TABLE research_tasks IS 'Background research tasks queue and results';
