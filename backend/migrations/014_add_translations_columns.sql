-- Add translations columns to messages and conversations tables
-- This enables storing pre-generated translations in all supported languages

-- Add translations column to messages table
-- Format: {"en": "text", "es": "texto", "fr": "texte", "de": "Text", "pt": "texto", "zh": "文本"}
ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS translations JSONB DEFAULT NULL;

-- Add title_translations column to conversations table
-- Format: {"en": "title", "es": "título", "fr": "titre", "de": "Titel", "pt": "título", "zh": "标题"}
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS title_translations JSONB DEFAULT NULL;

-- Add index for faster queries on translations
CREATE INDEX IF NOT EXISTS idx_messages_translations ON messages USING gin(translations);
CREATE INDEX IF NOT EXISTS idx_conversations_title_translations ON conversations USING gin(title_translations);

-- Comment explaining the structure
COMMENT ON COLUMN messages.translations IS 'Pre-generated translations of message content in all supported languages (en, es, fr, de, pt, zh)';
COMMENT ON COLUMN conversations.title_translations IS 'Pre-generated translations of conversation title in all supported languages (en, es, fr, de, pt, zh)';
