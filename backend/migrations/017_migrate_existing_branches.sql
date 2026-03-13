-- Migration: Move existing assistant messages to the new branching structure
-- The messages table has: id, conversation_id, user_id, role, content, metadata, created_at
-- There is no parent_id column, so we pair each assistant message with the
-- preceding user message by chronological order within each conversation.

-- 1. Pair assistant messages with the closest preceding user message
WITH ordered_messages AS (
    SELECT 
        id,
        conversation_id,
        role,
        content,
        metadata,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY conversation_id ORDER BY created_at ASC) as msg_order
    FROM messages
),
user_messages AS (
    SELECT id, conversation_id, msg_order
    FROM ordered_messages
    WHERE role = 'user'
),
assistant_with_parent AS (
    SELECT 
        a.id AS assistant_id,
        a.conversation_id,
        a.content,
        a.metadata,
        a.created_at,
        (
            SELECT u.id FROM user_messages u 
            WHERE u.conversation_id = a.conversation_id 
              AND u.msg_order < a.msg_order 
            ORDER BY u.msg_order DESC 
            LIMIT 1
        ) AS user_message_id
    FROM ordered_messages a
    WHERE a.role = 'assistant'
),
numbered AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY user_message_id ORDER BY created_at ASC) as branch_num
    FROM assistant_with_parent
    WHERE user_message_id IS NOT NULL
)
INSERT INTO assistant_responses (
    id, user_message_id, branch_label, content, metadata, created_at, updated_at
)
SELECT 
    assistant_id,
    user_message_id,
    CHR((64 + LEAST(branch_num, 26))::int),
    content,
    metadata,
    created_at,
    created_at
FROM numbered;

-- 2. Create branch selections (select the latest response per user message)
WITH latest AS (
    SELECT DISTINCT ON (ar.user_message_id)
        m.conversation_id,
        ar.user_message_id,
        ar.id AS active_response_id
    FROM assistant_responses ar
    JOIN messages m ON m.id = ar.user_message_id
    ORDER BY ar.user_message_id, ar.created_at DESC
)
INSERT INTO branch_selections (conversation_id, user_message_id, active_response_id)
SELECT conversation_id, user_message_id, active_response_id
FROM latest
ON CONFLICT (conversation_id, user_message_id)
DO UPDATE SET active_response_id = EXCLUDED.active_response_id;
