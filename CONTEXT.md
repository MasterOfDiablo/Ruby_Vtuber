
# Ruby VTuber Project: Contextual Documentation for Development AI

This document provides a detailed explanation of the Ruby VTuber project. It describes the purpose, design choices, and functionality of every part of the project to guide development by an AI or human developer. This document ensures that Ruby is developed according to the intended design and features while allowing for easy future expansion.

---

## Project Overview

Ruby is an AI-driven VTuber capable of:
1. **Interacting with viewers in real-time** using natural language processing (NLP).
2. **Expressing emotions visually and vocally** through a VTuber avatar using VTube Studio integration.
3. **Remembering game sessions and stream interactions**, enabling personalized responses and analytics.
4. **Streaming games like Minecraft and more challenging games like Elden Ring**, while actively engaging with viewers.

### Key Features
- **NLP-Driven Interaction**: Ruby uses AI to generate conversational responses in real-time, making interactions feel dynamic and personalized. Ruby processes a wide variety of viewer comments, providing engaging and contextually appropriate responses.
- **Emotional Intelligence**: Ruby can recognize, respond to, and express emotions. Emotional states are conveyed through both visual (avatar expressions) and auditory (voice modulation) cues, allowing for rich, nuanced viewer interactions. This helps create a stronger bond with the audience, making interactions feel more human.
- **Game and Stream Memory**: Ruby tracks and remembers game events, viewer interactions, and stream highlights, allowing her to maintain continuity of experience. Ruby can provide personalized callbacks, such as recalling a specific viewer's comment or referring to a previous in-game achievement.
- **Modular Design**: The project is highly modular, enabling easy feature additions, maintenance, and integration with other components. Each functionality is compartmentalized into its own module to simplify updates, scaling, and testing.

---

## Directory Structure

Here’s the complete project structure, with explanations of each component:

```
ruby/
├── .env                         # Environment variables
├── .gitignore                   # Git ignore file
├── config/                      # Configuration files
│   ├── settings.py              # Centralized settings
│   ├── expressions.json         # VTuber expressions mapping
├── sql/                         # SQL scripts
│   ├── create_tables.sql        # Schema creation
│   ├── test_setup.sql           # Test database setup
│   ├── test_cleanup.sql         # Test database cleanup
├── src/                         # Core source code
│   ├── ruby/                    # Main Ruby application logic               
│   │   ├── chat/                # AI logic for responses and personality
│   │   │   ├── core_logic.py    # Core AI logic for response generation
│   │   │   ├── context_manager.py # Manages conversational context
│   │   │   ├── emotion_handler.py # Emotion and sentiment analysis
│   │   │   └── __init__.py
│   │   ├── integrations/        # External service integrations
│   │   │   ├── vtube_studio/    # VTube Studio integration
│   │   │   │   ├── websocket.py # WebSocket communication
│   │   │   │   ├── expressions.py # Managing avatar expressions
│   │   │   │   ├── lip_sync.py  # Lip-sync and audio synchronization
│   │   │   │   └── __init__.py
│   │   │   ├── text_to_speech/  # Text-to-Speech integration
│   │   │   │   ├── generator.py # TTS generation logic
│   │   │   │   ├── playback.py  # Audio playback functionality
│   │   │   │   ├── emotion_mapper.py # Mapping emotions to voice styles
│   │   │   │   └── __init__.py
│   │   │   ├── database/        # Database interactions
│   │   │   │   ├── db_manager.py # Database manager for connections and queries
│   │   │   │   ├── game_queries.py # Queries for game-related data
│   │   │   │   ├── stream_queries.py # Queries for stream-related data
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   ├── memory/              # Memory and session tracking
│   │   │   ├── game_sessions/   # Game session management
│   │   │   │   ├── session_manager.py # Game session lifecycle management
│   │   │   │   ├── event_tracker.py # Game event tracking and logging
│   │   │   │   ├── analytics.py # Game analytics and metrics
│   │   │   │   └── __init__.py
│   │   │   ├── stream_sessions/ # Stream session management
│   │   │   │   ├── session_manager.py # Stream session lifecycle management
│   │   │   │   ├── highlight_tracker.py # Highlights and key moments
│   │   │   │   ├── interaction_manager.py # Viewer interaction tracking
│   │   │   │   ├── analytics.py # Stream analytics and engagement metrics
│   │   │   │   └── __init__.py
│   │   │   └── __init__.py
│   │   └── __init__.py
├── tests/                       # Testing modules
│   ├── integrations/            # Integration-specific tests
│   ├── memory/                  # Memory module tests
│   ├── ai/                      # AI module tests
│   └── __init__.py
├── data/                        # Static data
│   ├── personality.txt          # Personality traits
│   └── game_data/               # Game-specific static data
├── logs/                        # Log files
│   ├── app.log                  # General application logs
│   ├── error.log                # Error logs
├── CONTEXT.md                   # This contextual documentation
├── requirements.txt             # Python dependencies
├── venv/                        # Virtual environment (not tracked in Git)
```

---

### Detailed Explanation of Each Folder

#### **1. `.env`**
This file contains sensitive environment variables such as API keys, database credentials, and other configuration details. These are not hardcoded for security reasons.

- **Why**: This prevents sensitive data from being accidentally exposed in version control or shared with unauthorized collaborators. By keeping secrets outside of the core codebase, we ensure better security and flexibility.

---

#### **2. `.gitignore`**
The `.gitignore` file lists files and directories to be excluded from Git tracking. It ensures that sensitive or irrelevant files (e.g., `venv/`, logs) are not committed.

- **Why**: Ignoring these files helps maintain a clean repository. It also prevents sensitive information, unnecessary system-generated files, or temporary working directories from cluttering the project.

Example:
```
# Ignore virtual environment
venv/

# Ignore environment variables
.env

# Ignore logs
logs/
```

---

#### **3. `config/`**
Stores static configuration files.

- **`settings.py`**: Centralizes settings, such as API endpoints, default parameters, and feature toggles. This keeps configuration in one place, making it easy to update as requirements change.
- **`expressions.json`**: Maps emotional states to specific VTube Studio expressions. This allows Ruby to visually express various emotions in a way that matches her tone of voice during interactions.

- **Why**: Keeping configurations in dedicated files makes it easy to adapt Ruby's behavior, emotion mappings, or system parameters without altering the core logic.

---

#### **4. `sql/`**
Contains SQL scripts for database schema and testing.

- **`create_tables.sql`**: Defines the structure of database tables, including user interactions, session tracking, and other core data.
- **`test_setup.sql`** and **`test_cleanup.sql`**: Scripts for setting up test data and tearing it down afterward. This is critical for consistent unit testing and validation of features that rely on database operations.

- **Why**: Predefined SQL scripts help maintain consistency and speed up deployment and testing of the database layer.

---

#### **5. `src/ruby/`**
The core application logic resides here, organized into submodules.

---

##### **`chat/`**
Handles Ruby’s personality and conversational logic.

- **`core_logic.py`**:
  - Generates responses using OpenAI or similar NLP APIs. The main goal is to generate natural and engaging responses to viewer input.
  - Includes fallback mechanisms for error handling, ensuring that Ruby can continue to operate smoothly even if the AI API returns errors or unexpected results.
- **`context_manager.py`**:
  - Tracks the context of conversations to enable coherent replies. For instance, if a viewer asks a follow-up question, Ruby should remember the previous topic to respond appropriately.
  - Supports context switching for topic changes, allowing Ruby to smoothly transition between different topics during a conversation.
- **`emotion_handler.py`**:
  - Analyzes sentiment from viewer inputs and adjusts Ruby’s emotional state accordingly. For example, Ruby can recognize excitement in chat messages and respond with enthusiasm.
  - Maps emotions to visual expressions and vocal tones so that Ruby's responses feel more alive and interactive.

- **Why**: Splitting AI logic into distinct submodules allows for improved focus on different areas of interaction, such as managing context or adjusting emotions. This separation enhances readability and maintainability.

---

##### **`integrations/`**
Connects Ruby to external services like VTube Studio, TTS, and the database.

- **`vtube_studio/`**:
  - **`websocket.py`**: Manages WebSocket communication with VTube Studio, ensuring real-time control of Ruby's avatar.
  - **`expressions.py`**: Maps Ruby’s emotions to specific avatar expressions, providing a visual representation of how Ruby is feeling.
  - **`lip_sync.py`**: Synchronizes TTS audio with avatar lip movements, making the visual experience more authentic by matching lip movement with spoken words.
- **`text_to_speech/`**:
  - **`generator.py`**: Uses TTS APIs (e.g., Google TTS, ElevenLabs) to generate voice output that matches the given text. Ruby's spoken words are synthesized here.
  - **`playback.py`**: Plays audio files generated by TTS, allowing Ruby's voice to be heard by viewers.
  - **`emotion_mapper.py`**: Modifies TTS output to reflect Ruby’s emotional tone. For example, excitement could be expressed by increasing pitch and speed.
- **`database/`**:
  - **`db_manager.py`**: Manages connections and queries to the database. It abstracts database logic from core code, improving maintainability.
  - **`game_queries.py`**: Specialized queries for game memory data, such as tracking achievements or deaths in Elden Ring.
  - **`stream_queries.py`**: Specialized queries for stream memory data, enabling Ruby to keep track of viewer comments, highlights, and interactions across different sessions.

- **Why**: Integration modules are kept separate so that updates to one service do not impact others. This modularity allows for swapping or updating individual integrations without affecting the rest of Ruby's functionality.

---

##### **`memory/`**
Manages Ruby’s memory for game sessions and streams.

- **`game_sessions/`**:
  - **`session_manager.py`**: Handles lifecycle events for game sessions, such as when a new game starts, pauses, or ends. Tracks progress during challenging games like Elden Ring.
  - **`event_tracker.py`**: Logs key game events (e.g., deaths, achievements). This helps Ruby remember past gameplay, providing continuity between sessions.
  - **`analytics.py`**: Provides advanced metrics and analysis for gameplay, such as how many times Ruby died at a specific boss or how her strategy evolved.
- **`stream_sessions/`**:
  - **`session_manager.py`**: Manages active stream sessions, including start, end, and pauses, ensuring that all relevant data is correctly logged.
  - **`highlight_tracker.py`**: Identifies and logs stream highlights (e.g., large donations, intense combat moments) to create engaging summaries or callbacks.
  - **`interaction_manager.py`**: Tracks viewer interactions like chat messages, subscriptions, and recurring viewers. Allows Ruby to provide personalized shout-outs or recall interactions.
  - **`analytics.py`**: Analyzes stream engagement metrics (e.g., average chat rate, viewer retention) to provide insights into stream performance.

- **Why**: By separating game and stream memory into different modules, we maintain clear boundaries between the different types of experiences Ruby can recall. Each submodule handles specific tasks that improve scalability and simplify maintenance.

---

#### **6. `tests/`**
Contains test cases to validate each module.

- Mirrors the structure of `src/ruby` for easy test mapping.
- Example: `tests/integrations/test_text_to_speech.py` tests `src/ruby/integrations/text_to_speech/`.
- **Why**: Having a parallel structure for tests ensures that every functionality is covered, which simplifies debugging and reduces the risk of untested code being deployed.

---

#### **7. `data/`**
Static data used by the application.

- **`personality.txt`**: Defines Ruby’s personality traits, including aspects like humor, formality, and style of communication. This ensures that Ruby maintains a consistent character.
- **`game_data/`**: Stores static game-related data like predefined events, key milestones, or metadata about the games Ruby plays (e.g., maps, boss strategies).

- **Why**: Storing this information in separate data files allows for easy updates without touching the core logic.

---

#### **8. `logs/`**
Stores logs generated by the application.

- **`app.log`**: General runtime logs that track application events, actions taken, and significant occurrences during runtime.
- **`error.log`**: Logs for debugging errors, storing stack traces, and other error-related information that assists in troubleshooting issues.

- **Why**: Logs are critical for understanding how Ruby behaves over time and for diagnosing any issues that arise. Having separate logs for general events and errors helps keep information organized.


#### **10. `requirements.txt`**
Lists Python dependencies, ensuring the environment can be set up consistently.

- **Why**: By specifying dependencies, anyone setting up the project can install the exact versions of libraries used, ensuring compatibility and reducing bugs caused by version mismatches.

Example:
```
openai==0.27.0
websockets==10.3
```

---

#### **11. `venv/`**
A virtual environment for isolating dependencies. Not tracked in Git.

- **Why**: A virtual environment allows all dependencies to be contained, preventing conflicts with other Python projects on the same machine. It ensures that Ruby’s required libraries don’t interfere with system-level packages or other projects.

---

This detailed explanation provides the necessary guidance for any developer or AI tasked with implementing Ruby VTuber, including the reasoning behind each decision and how each module interacts within the broader project.
