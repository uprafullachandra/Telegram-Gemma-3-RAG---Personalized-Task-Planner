# GemmaRAG Personal Assistant

A personal assistant powered by Gemma 3 and Chroma vector database, integrated with Telegram.

## Features

- Task management with priority codes
- Mood/reflection tracking
- Daily planning with context awareness
- Natural language queries
- Local model operation (no API keys needed)

## Priority Codes

- **Ferrari**: urgent and important
- **Tesla**: semi-urgent and important
- **Amazon**: not urgent but important
- **Suzuki**: urgent, not important but necessary
- **Orange**: semi-urgent, not important but eventually necessary
- **Budweiser**: not important not urgent
- **Greyhound**: semi-complete needs follow up

## Setup Instructions

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Set Up Telegram Bot

1. Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Create a new bot with `/newbot`
3. Get your token and set it as an environment variable:

```bash
# Linux/Mac
export TELEGRAM_TOKEN="your_token_here"

# Windows
set TELEGRAM_TOKEN=your_token_here
```

### 3. Install and Start Ollama

1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Install and start Ollama
3. Pull and run the Gemma 3:1b model:

```bash
ollama run gemma3:1b
```

### 4. Run the Bot

```bash
python main.py
```

## Available Commands

- `/start` - Initialize the bot
- `/help` - Show available commands
- `/add_task [text]` - Add a new task (include priority code in text)
- `/complete_task [task_id]` - Mark a task as completed
- `/add_reflection [text]` - Add a reflection with optional mood score (e.g., "Today was good 8/10")
- `/plan_day` - Generate a day plan based on current tasks

## Example Usage

- "Add task: Finish the report by Friday. Ferrari"
- "Show me my Tesla tasks"
- "What tasks do I need to complete today?"
- "/add_reflection Today I felt productive and accomplished a lot, even though I was a bit tired. 7/10"