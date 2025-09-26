# Requirements Document

## Introduction

This feature involves enhancing the user interface of the existing Pharmacology Chat Assistant application. The improvements focus on simplifying the user profile display, modernizing the model selection interface, enforcing a consistent dark theme throughout the application, and increasing the token limits for premium users to provide better conversational experiences.

## Requirements

### Requirement 1

**User Story:** As a user, I want unnecessary elements removed from the sidebar, so that I have a cleaner and more focused interface.

#### Acceptance Criteria

1. WHEN a user views the sidebar THEN the system SHALL NOT display any plan or subscription tier information
2. WHEN the sidebar is rendered THEN it SHALL NOT show any dropdown for choosing messages per conversation
3. WHEN the sidebar is displayed THEN it SHALL NOT show pagination controls or page size selectors
4. WHEN users interact with the sidebar THEN they SHALL not see any references to "Free", "Premium", or other plan designations
5. WHEN the sidebar loads THEN it SHALL only contain essential user controls like logout and model selection

### Requirement 2

**User Story:** As a user, I want the model selection to be a toggle switch instead of a dropdown, so that I can quickly switch between fast and premium modes with a more intuitive interface.

#### Acceptance Criteria

1. WHEN a user accesses model selection THEN they SHALL see a toggle switch interface instead of a dropdown menu
2. WHEN the toggle is in the left position THEN the system SHALL use the fast model (Gemma2-9B-IT)
3. WHEN the toggle is in the right position THEN the system SHALL use the premium model (Qwen3-32B)
4. WHEN a user clicks the toggle THEN the system SHALL immediately switch models and provide visual feedback
5. WHEN the toggle is displayed THEN it SHALL clearly indicate which mode is currently active with appropriate labels and styling

### Requirement 3

**User Story:** As a user, I want the application to use dark mode permanently throughout the entire interface, so that I have a consistent and comfortable viewing experience that is easy on the eyes.

#### Acceptance Criteria

1. WHEN a user accesses any part of the application THEN the system SHALL display everything in dark mode
2. WHEN the application loads THEN it SHALL NOT provide theme switching options or light mode alternatives
3. WHEN displaying text content THEN the system SHALL ensure high contrast and readability with appropriate text colors
4. WHEN rendering UI components THEN all elements SHALL use dark theme colors including backgrounds, borders, and accents
5. WHEN users view chat messages THEN both user and AI message bubbles SHALL use dark-themed styling that maintains readability

### Requirement 4

**User Story:** As a user, I want the premium mode to have an increased token limit of 8,000 tokens, so that I can have longer and more detailed conversations without being constrained by token limitations.

#### Acceptance Criteria

1. WHEN a user selects premium mode THEN the system SHALL set the maximum token limit to 8,000 tokens
2. WHEN generating responses in premium mode THEN the system SHALL allow for longer, more comprehensive answers up to 8,000 tokens
3. WHEN premium mode is active THEN the system SHALL maintain context for longer conversations without truncation
4. WHEN the 8,000 token limit is applied THEN the system SHALL ensure responses can be more detailed and thorough
5. WHEN fast mode is selected THEN the system SHALL maintain the existing lower token limits for performance

### Requirement 5

**User Story:** As a user, I want unlimited conversation history display without pagination controls, so that I can view my entire conversation seamlessly without restrictions.

#### Acceptance Criteria

1. WHEN a user views their conversation history THEN the system SHALL display all messages without pagination
2. WHEN the conversation history loads THEN the system SHALL NOT show any dropdown for selecting messages per page
3. WHEN a user scrolls through their conversation THEN they SHALL see their complete chat history
4. WHEN the interface renders THEN it SHALL remove all pagination controls and page size selectors
5. WHEN displaying long conversations THEN the system SHALL optimize performance while showing unlimited messages

### Requirement 6

**User Story:** As a user, I want a tab for creating new conversations, so that I can organize my chats into separate conversation threads.

#### Acceptance Criteria

1. WHEN a user accesses the chat interface THEN they SHALL see a tab or button for creating new conversations
2. WHEN a user clicks the new conversation option THEN the system SHALL start a fresh conversation thread
3. WHEN multiple conversations exist THEN the system SHALL provide a way to switch between them
4. WHEN a new conversation is created THEN it SHALL be isolated from previous conversation history
5. WHEN managing conversations THEN the system SHALL allow users to organize and navigate between different chat sessions

### Requirement 7

**User Story:** As a user, I want the RAG system to properly process my uploaded documents and use them as context for my prompts, so that I can get relevant answers based on my specific documents.

#### Acceptance Criteria

1. WHEN a user uploads a document THEN the system SHALL successfully process and extract text content
2. WHEN documents are processed THEN the system SHALL generate embeddings and store them in the vector database
3. WHEN a user asks a question THEN the system SHALL retrieve relevant context from uploaded documents
4. WHEN generating responses THEN the system SHALL incorporate document context into the AI's answers
5. WHEN the RAG pipeline runs THEN it SHALL provide clear feedback about document processing status and success