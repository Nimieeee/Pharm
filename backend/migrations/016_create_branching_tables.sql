-- Migration: Create independent branching tables (assistant_responses & branch_selections)

-- 1. Create assistant_responses table
CREATE TABLE assistant_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    branch_label TEXT NOT NULL DEFAULT 'A',
    content TEXT NOT NULL,
    model_used TEXT,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Create branch_selections table
CREATE TABLE branch_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    active_response_id UUID REFERENCES assistant_responses(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(conversation_id, user_message_id)
);

-- 3. Create indexes for performance
CREATE INDEX idx_responses_user_msg ON assistant_responses(user_message_id);
CREATE INDEX idx_selections_conv ON branch_selections(conversation_id);
CREATE INDEX idx_selections_user_msg ON branch_selections(user_message_id);
CREATE INDEX idx_responses_created_at ON assistant_responses(created_at);

-- 4. Set up Row Level Security (RLS)
-- We need to restrict access based on the conversation owner
ALTER TABLE assistant_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE branch_selections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read/write responses in their own conversations
CREATE POLICY "Users can access their own assistant responses" 
ON assistant_responses 
FOR ALL 
USING (
    user_message_id IN (
        SELECT m.id FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = auth.uid()
    )
);

-- Policy: Users can read/write branch selections in their own conversations
CREATE POLICY "Users can access their own branch selections" 
ON branch_selections 
FOR ALL 
USING (
    conversation_id IN (
        SELECT id FROM conversations WHERE user_id = auth.uid()
    )
);

-- 5. Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_assistant_responses_updated_at
    BEFORE UPDATE ON assistant_responses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_branch_selections_updated_at
    BEFORE UPDATE ON branch_selections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
