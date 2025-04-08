import re
from db_setup import get_chroma_collection
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
import os
import time
import logging
from task_manager import add_task, complete_task, query_tasks, add_reflection, PRIORITIES
from gemma_integration import generate_text

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    await update.message.reply_text(
        "Hello! I'm Halsey, your GemmaRAG assistant powered by Gemma 3. "
        "I can help you manage tasks and plan your day. "
        "Use /help to see available commands."
    )

async def help_command(update, context):
    help_text = (
        "🤖 *Halsey Bot Commands:*\n\n"
        "/start - Initialize the bot\n"
        "/add_task [text] - Add a new task (include priority code in text)\n"
        "/complete_task [task_id] - Mark a task as completed\n"
        "/add_reflection [text] - Add a reflection with optional mood score (e.g., 'Today was good 8/10')\n"
        "/plan_day - Generate a day plan based on current tasks\n"
        "/help - Show this help message\n\n"
        
        "You can also ask me natural language questions like:\n"
        "- 'Show me my Ferrari tasks'\n"
        "- 'What tasks do I need to complete today?'\n"
        "- 'How am I feeling this week?'\n\n"
        
        "*Priority Codes:*\n"
        "- Ferrari: urgent and important\n"
        "- Tesla: semi-urgent and important\n"
        "- Amazon: not urgent but important\n"
        "- Suzuki: urgent, not important but necessary\n"
        "- Orange: semi-urgent, not important but eventually necessary\n"
        "- Budweiser: not important not urgent\n"
        "- Greyhound: semi-complete needs follow up"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def add_task_command(update, context):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Please provide task details after /add_task.")
        return
    
    # Check if priority code is provided
    priority = None
    for code in PRIORITIES:
        if code.lower() in text.lower():
            priority = code
            break
    
    task_id, metadata = add_task(text, priority)
    priority_info = f"Priority: {metadata.get('priority_description', 'Not specified')}" if metadata.get('priority_code') else ""
    
    await update.message.reply_text(f"Task stored! ID: {task_id}\n{priority_info}")

async def complete_task_command(update, context):
    if not context.args:
        await update.message.reply_text("Please provide task ID after /complete_task.")
        return
    
    task_id = context.args[0]
    success, message = complete_task(task_id)
    await update.message.reply_text(message)

async def add_reflection_command(update, context):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Please provide reflection details after /add_reflection.")
        return
    
    # Check for mood score in format "7/10" or similar
    mood_score = None
    match = re.search(r'(\d+)\s*\/\s*10', text)
    if match:
        mood_score = int(match.group(1))
        if mood_score < 0:
            mood_score = 0
        elif mood_score > 10:
            mood_score = 10
    
    reflection_id, metadata = add_reflection(text, mood_score)
    mood_info = f"Mood score: {metadata['mood_score']}/10" if 'mood_score' in metadata else ""
    
    await update.message.reply_text(f"Reflection stored! ID: {reflection_id}\n{mood_info}")

async def plan_day_command(update, context):
    # Get today's date
    today = time.strftime("%Y-%m-%d")
    
    await update.message.reply_text("Generating your day plan... This might take a moment.")
    
    # Query all incomplete tasks
    collection = get_chroma_collection()
    results = collection.get(
        where={"completed": False}
    )

    # Then filter tasks of type "task"
    filtered_results = {
    "documents": [],
    "metadatas": [],
    "ids": []
    }

    for doc, meta, task_id in zip(results["documents"], results["metadatas"], results["ids"]):
     if meta.get("type") == "task":
        filtered_results["documents"].append(doc)
        filtered_results["metadatas"].append(meta)
        filtered_results["ids"].append(task_id)

    
    # Get recent reflections
    reflection_results = collection.get(
        where={"type": "reflection"},
        limit=3
    )
    
    # Prepare tasks for Gemma
    tasks_by_priority = {}
    for doc, meta, task_id in zip(results["documents"], results["metadatas"], results["ids"]):
        priority = meta.get("priority_code", "unknown")
        if priority not in tasks_by_priority:
            tasks_by_priority[priority] = []
        tasks_by_priority[priority].append({"id": task_id, "text": doc})
    
    # Build prompt for Gemma
    prompt = f"Today is {today}. Please create a balanced day plan for me based on these tasks:\n\n"
    
    # Add tasks by priority
    for priority in ["ferrari", "tesla", "amazon", "suzuki", "orange", "greyhound", "budweiser"]:
        if priority in tasks_by_priority:
            prompt += f"{priority.upper()} TASKS ({PRIORITIES[priority]}):\n"
            for task in tasks_by_priority[priority]:
                prompt += f"- {task['text']} (ID: {task['id']})\n"
            prompt += "\n"
    
    # Add recent reflections for context
    if reflection_results["documents"]:
        prompt += "Recent reflections:\n"
        for doc, meta in zip(reflection_results["documents"], reflection_results["metadatas"]):
            date = meta.get("created_at", "unknown date")
            mood = f"Mood: {meta.get('mood_score', '?')}/10" if "mood_score" in meta else ""
            prompt += f"- [{date}] {doc} {mood}\n"
    
    prompt += "\nBased on this information, create a balanced day plan that:\n"
    prompt += "1. Prioritizes Ferrari and Tesla tasks\n"
    prompt += "2. Includes breaks and self-care\n"
    prompt += "3. Is realistic and achievable\n"
    prompt += "4. Groups similar tasks together when possible\n"
    prompt += "Please format the plan with time blocks."
    
    # Generate plan with Gemma 3
    plan = generate_text(prompt)
    await update.message.reply_text(f"Here's your plan for today:\n\n{plan}")

async def handle_message(update, context):
    user_input = update.message.text
    
    # Check if this is a task creation request
    if any(keyword in user_input.lower() for keyword in ["add task", "new task", "create task"]):
        for code in PRIORITIES:
            if code.lower() in user_input.lower():
                task_id, metadata = add_task(user_input)
                await update.message.reply_text(f"Task added! ID: {task_id}\nPriority: {metadata.get('priority_description', 'Not specified')}")
                return
    
    # Check if this is a task query
    if any(keyword in user_input.lower() for keyword in ["find task", "show task", "list task", "my task"]):
        # Determine if user wants specific priorities
        filter_metadata = {}
        for code in PRIORITIES:
            if code.lower() in user_input.lower():
                filter_metadata["priority_code"] = code.lower()
                break
        
        # Handle completion status filtering
        if "completed" in user_input.lower():
            filter_metadata["completed"] = True
        elif "incomplete" in user_input.lower() or "not done" in user_input.lower():
            filter_metadata["completed"] = False
        
        results = query_tasks(user_input, filter_metadata=filter_metadata)
        
        if not results["documents"] or len(results["documents"][0]) == 0:
            await update.message.reply_text("No matching tasks found.")
            return
        
        # Format the results
        response = "Here are your tasks:\n\n"
        for i, (doc, meta, id) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["ids"][0])):
            status = "✓ DONE" if meta.get("completed", False) else "◯ PENDING"
            priority = f"[{meta.get('priority_code', 'Unknown').upper()}]" if meta.get("priority_code") else ""
            response += f"{i+1}. {status} {priority} {doc}\nID: {id}\n\n"
        
        await update.message.reply_text(response)
        return
    
    # For other queries, use Gemma with retrieved context
    await update.message.reply_text("Thinking...")
    
    # Get relevant tasks for context
    task_results = query_tasks(user_input, top_k=3)
    
    # Get relevant reflections for context
    from db_setup import get_chroma_collection
    reflection_results = get_chroma_collection().query(
        query_embeddings=[embed_texts([user_input])[0]],
        n_results=2,
        where={"type": "reflection"}
    )
    
    # Build context from retrieved documents
    context_docs = []
    if task_results["documents"] and task_results["documents"][0]:
        for doc, meta in zip(task_results["documents"][0], task_results["metadatas"][0]):
            status = "completed" if meta.get("completed", False) else "pending"
            priority = f"{meta.get('priority_code', 'unknown')} ({meta.get('priority_description', '')})" if meta.get("priority_code") else "no priority"
            context_docs.append(f"Task: {doc} | Status: {status} | Priority: {priority}")
    
    # Add relevant reflections to context
    if reflection_results["documents"] and reflection_results["documents"][0]:
        for doc, meta in zip(reflection_results["documents"][0], reflection_results["metadatas"][0]):
            date = meta.get("created_at", "unknown date")
            mood = f"Mood: {meta.get('mood_score', '?')}/10" if "mood_score" in meta else ""
            context_docs.append(f"Reflection [{date}]: {doc} {mood}")
    
    context_block = "\n".join(context_docs) if context_docs else "No relevant information found."
    
    # Create prompt for Gemma 3
    prompt = (
        f"The user is asking: '{user_input}'\n\n"
        f"Relevant information from their database:\n{context_block}\n\n"
        "Here are the priority codes they use:\n"
        "- Ferrari: urgent and important\n"
        "- Tesla: semi-urgent and important\n"
        "- Amazon: not urgent but important\n"
        "- Suzuki: urgent, not important but necessary\n"
        "- Orange: semi-urgent, not important but eventually necessary\n"
        "- Budweiser: not important not urgent\n"
        "- Greyhound: semi-complete needs follow up\n\n"
        "Based on the above information, please provide a helpful, concise response that addresses the user's query:"
    )
    
    # Generate response from Gemma 3
    response = generate_text(prompt)
    await update.message.reply_text(response)

async def error_handler(update, context):
    """Log Errors caused by Updates."""
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    if update:
        await update.message.reply_text("Sorry, something went wrong. Please try again.")

def main():
    # Get the token from environment variable
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    
    if not telegram_token:
        print("Error: TELEGRAM_TOKEN environment variable not set.")
        print("Please set it with: export TELEGRAM_TOKEN='your_token_here'")
        return
    
    # Create the Updater and pass it your bot's token
    #updater = Updater(token=telegram_token, use_context=True)
    application = ApplicationBuilder().token(telegram_token).build()
    
    # Get the dispatcher to register handlers
    #dp = updater.dispatcher
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add_task", add_task_command))
    application.add_handler(CommandHandler("complete_task", complete_task_command))
    application.add_handler(CommandHandler("add_reflection", add_reflection_command))
    application.add_handler(CommandHandler("plan_day", plan_day_command))
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    print("Starting bot...")
    application.run_polling()
    
    # Run the bot until you press Ctrl-C
    print("Bot is running! Press Ctrl+C to stop.")
    #application.idle()

# Import needed for handle_message function
from embeddings import embed_texts

if __name__ == "__main__":
    main()