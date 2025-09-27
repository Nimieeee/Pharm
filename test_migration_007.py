#!/usr/bin/env python3
"""
Test script for migration 007 - Document Processing Status
Validates the SQL syntax and structure of the document processing status migration.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_migration_syntax():
    """Validate the SQL syntax of migration 007."""
    migration_file = Path('migrations/007_document_processing_status.sql')
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Basic syntax validation
        required_elements = [
            'CREATE TABLE IF NOT EXISTS document_processing_status',
            'CREATE INDEX IF NOT EXISTS idx_document_processing_user_id',
            'CREATE INDEX IF NOT EXISTS idx_document_processing_status',
            'CREATE INDEX IF NOT EXISTS idx_document_processing_user_status',
            'CREATE INDEX IF NOT EXISTS idx_document_processing_created_at',
            'ALTER TABLE document_processing_status ENABLE ROW LEVEL SECURITY',
            'CREATE POLICY "Users can view own document processing status"',
            'CREATE OR REPLACE FUNCTION update_document_processing_timestamp()',
            'CREATE TRIGGER update_document_processing_status_timestamp',
            'CREATE OR REPLACE FUNCTION get_user_document_processing_status',
            'CREATE OR REPLACE FUNCTION get_document_processing_summary',
            'CREATE OR REPLACE FUNCTION cleanup_old_document_processing_records'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in sql_content:
                missing_elements.append(element)
        
        if missing_elements:
            logger.error("Missing required SQL elements:")
            for element in missing_elements:
                logger.error(f"  - {element}")
            return False
        
        # Check for required columns
        required_columns = [
            'id UUID PRIMARY KEY',
            'user_id UUID REFERENCES users(id)',
            'filename TEXT NOT NULL',
            'original_filename TEXT NOT NULL',
            'file_size BIGINT',
            'mime_type TEXT',
            'status TEXT NOT NULL CHECK',
            'chunks_created INTEGER DEFAULT 0',
            'embeddings_stored INTEGER DEFAULT 0',
            'error_message TEXT',
            'processing_started_at TIMESTAMP WITH TIME ZONE',
            'processing_completed_at TIMESTAMP WITH TIME ZONE',
            'created_at TIMESTAMP WITH TIME ZONE',
            'updated_at TIMESTAMP WITH TIME ZONE'
        ]
        
        missing_columns = []
        for column in required_columns:
            if column not in sql_content:
                missing_columns.append(column)
        
        if missing_columns:
            logger.error("Missing required columns:")
            for column in missing_columns:
                logger.error(f"  - {column}")
            return False
        
        logger.info("✅ Migration 007 syntax validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating migration syntax: {e}")
        return False

def check_task_requirements():
    """Check if all task requirements are met."""
    logger.info("Checking task requirements...")
    
    # Check if conversation management migration exists (task requirement)
    conv_migration = Path('migrations/006_conversation_management.sql')
    if not conv_migration.exists():
        logger.error("❌ Conversation management migration (006) not found")
        return False
    
    # Check if document processing migration exists
    doc_migration = Path('migrations/007_document_processing_status.sql')
    if not doc_migration.exists():
        logger.error("❌ Document processing status migration (007) not found")
        return False
    
    # Validate conversation management migration has required elements
    try:
        with open(conv_migration, 'r') as f:
            conv_content = f.read()
        
        conv_requirements = [
            'CREATE TABLE IF NOT EXISTS conversations',
            'ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id',
            'CREATE INDEX IF NOT EXISTS idx_conversations_user_id',
            'CREATE INDEX IF NOT EXISTS idx_messages_conversation'
        ]
        
        for req in conv_requirements:
            if req not in conv_content:
                logger.error(f"❌ Missing in conversation migration: {req}")
                return False
        
        logger.info("✅ Conversation management migration requirements met")
        
    except Exception as e:
        logger.error(f"Error checking conversation migration: {e}")
        return False
    
    logger.info("✅ All task requirements validated successfully")
    return True

def main():
    """Main test function."""
    logger.info("Starting migration 007 validation...")
    
    # Validate syntax
    if not validate_migration_syntax():
        logger.error("❌ Migration syntax validation failed")
        return False
    
    # Check task requirements
    if not check_task_requirements():
        logger.error("❌ Task requirements validation failed")
        return False
    
    logger.info("🎉 All validations passed! Migration 007 is ready.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)