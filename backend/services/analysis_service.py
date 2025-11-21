"""Service for analyzing and summarizing SQL query results using GPT"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Set up logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def detect_analysis_request(message: str) -> bool:
    """Detect if user is requesting analysis or summarization of previous response data"""
    message_lower = message.lower()
    analysis_keywords = [
        'analyze', 'analysis', 'summarize', 'summary', 'summarization',
        'explain', 'explain me', 'explain the data', 'explain the response',
        'explain the results', 'explain these results', 'explain this data',
        'what does this data show', 'what does this show', 'what is this data',
        'insights', 'findings', 'interpret', 'interpretation', 
        'overview', 'breakdown', 'tell me about', 'describe the data', 
        'what can you tell me about', 'summarize me', 'explain the above'
    ]
    return any(keyword in message_lower for keyword in analysis_keywords)

def analyze_data_with_gpt(
    data: List[Dict[str, Any]], 
    user_question: str,
    analysis_question: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> str:
    """
    Analyze and summarize query results using GPT based on user's question
    
    Args:
        data: The query results to analyze
        user_question: The original user question that generated this data
        analysis_question: The NEW question the user is asking about the data (if different from user_question)
        model: GPT model to use for analysis
    
    Returns:
        Analysis/summary text from GPT that answers the user's question
    """
    if not data or len(data) == 0:
        return "No data available to analyze."
    
    try:
        # Use the analysis_question if provided, otherwise use user_question
        question_to_answer = analysis_question if analysis_question else user_question
        
        # Limit data size to avoid token limits (analyze first 100 rows for stats, show sample)
        data_to_analyze = data[:100]
        total_rows = len(data)
        
        # Prepare data summary for GPT
        columns = list(data[0].keys()) if data else []
        
        # Calculate basic statistics for numeric columns
        stats = {}
        for col in columns:
            values = [row.get(col) for row in data_to_analyze if row.get(col) is not None]
            if values:
                first_val = values[0]
                if isinstance(first_val, (int, float)):
                    stats[col] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values) if values else 0,
                        "count": len(values)
                    }
        
        # Create a sample of the data (first 20 rows for context)
        data_sample = data_to_analyze[:20]
        
        # Determine if user wants explanation or summary (check the question they're asking NOW)
        is_explanation = any(word in question_to_answer.lower() for word in ['explain', 'explanation', 'what does', 'what is', 'how', 'which', 'best', 'most'])
        is_summary = any(word in question_to_answer.lower() for word in ['summarize', 'summary', 'overview', 'brief'])
        
        # Build the prompt based on user intent
        if is_explanation:
            task_instruction = f"""Your task is to EXPLAIN the data based on the user's question: "{question_to_answer}"

The user is asking: "{question_to_answer}"
The data below was retrieved from a previous query. Now the user wants you to answer this NEW question about that data.

Answer the user's question directly using the data provided. Explain:
- What the data shows in relation to their question
- Key findings that answer their question
- Important patterns or insights relevant to their question
- Any notable observations that help answer their question

Be specific and use actual numbers/values from the data to support your explanation."""
        elif is_summary:
            task_instruction = f"""Your task is to SUMMARIZE the data based on the user's question: "{question_to_answer}"

The user is asking: "{question_to_answer}"
The data below was retrieved from a previous query. Now the user wants you to answer this NEW question about that data.

Provide a concise summary that:
- Directly addresses the user's question
- Highlights the most important findings
- Provides key statistics or numbers
- Gives a clear overview of what the data reveals about their question"""
        else:
            task_instruction = f"""Your task is to ANALYZE the data based on the user's question: "{question_to_answer}"

The user is asking: "{question_to_answer}"
The data below was retrieved from a previous query. Now the user wants you to answer this NEW question about that data.

Provide a comprehensive analysis that:
- Directly answers the user's question using the data
- Identifies key insights and patterns relevant to their question
- Highlights important statistics, trends, or findings
- Explains what the data reveals about their specific question"""
        
        # Build the full context
        context = f"""{task_instruction}

IMPORTANT: The user is asking: "{question_to_answer}"
You MUST answer this specific question using ONLY the actual data provided below.

Context: This data was originally retrieved in response to: "{user_question}"
But now the user is asking a NEW question about this data: "{question_to_answer}"

Data Information:
- Total Rows: {total_rows:,}
- Column Names: {', '.join(columns)}
- These are the EXACT column names in the data - use them as they appear

"""
        
        # Add statistics if available
        if stats:
            context += "Key Statistics:\n"
            for col, stat in stats.items():
                context += f"- {col}: Min={stat['min']}, Max={stat['max']}, Avg={stat['avg']:.2f}, Count={stat['count']}\n"
            context += "\n"
        
        # Add sample data with clear instructions
        context += f"\nACTUAL DATA FROM THE DATABASE (first {len(data_sample)} rows of {total_rows:,} total):\n"
        context += "Look at the EXACT column names and values below. Use ONLY this data:\n\n"
        context += json.dumps(data_sample, indent=2, default=str)
        
        if total_rows > len(data_sample):
            context += f"\n\nNote: This is a sample of {len(data_sample)} rows. There are {total_rows:,} total rows in the results."
        
        context += f"\n\nREMEMBER: Answer the user's question '{question_to_answer}' using ONLY the actual data shown above. Do NOT make assumptions about what the data contains. Use the exact column names and values provided."
        
        messages = [
            {
                "role": "system", 
                "content": """You are a helpful data analyst. Your job is to explain data in a clear, conversational, and human-friendly way.

CRITICAL RULES:
1. **USE ONLY THE ACTUAL DATA PROVIDED** - Look at the exact column names and values in the sample data. Do NOT make assumptions or guess what the data contains.
2. **Answer ONLY what the user asked** - Be specific and focused on their exact question
3. **Identify the actual columns** - Use the exact column names from the data (e.g., PR_CODE, PR_DESC, BR_CODE, CT_CODE, etc.)
4. **Use actual values from the data** - Reference specific products, codes, or values that appear in the sample data
5. **For "best product" questions** - If the user asks which is the "best" product, identify it based on available criteria:
   - If price columns exist (PR_SELLING_PRICE, PR_FOB_PRICE), consider value
   - If stock columns exist (PR_STOCK_ONHAND), consider availability
   - If sales columns exist, consider popularity
   - If no clear criteria, state that and explain what data is available
6. Write in a natural, conversational tone - like you're explaining to a colleague
7. Use simple language - avoid jargon unless necessary
8. Be concise - get to the point quickly
9. Format your response in clear paragraphs with line breaks
10. Don't use bullet points or numbered lists unless absolutely necessary

Example of good explanation:
"Looking at the product data, I can see 1,000 products listed. The products range from '010AK HARD DISK CABLE' to various other items. To determine the 'best' product, I'd need more information like selling price, stock levels, or sales data. Based on what's available, I can see product codes and descriptions, but without pricing or performance metrics, I cannot definitively say which is the 'best' product."

Example of bad explanation:
"The data you provided on the 'edc category' consists of 1,000 entries..." (WRONG - this is making up information not in the data)"""
            },
            {
                "role": "user", 
                "content": context
            }
        ]
        
        logger.info(f"🔵 [{model}] Analyzing {total_rows} rows of data with GPT...")
        logger.info(f"📝 User Question: {user_question}")
        logger.info(f"📝 Analysis Question: {question_to_answer}")
        
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,  # Slightly higher for more creative analysis
                max_tokens=800,  # Reduced for more concise explanations
                timeout=60.0  # 60 second timeout for analysis
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.info(f"✅ [{model}] Analysis completed")
            
            return analysis
        except Exception as api_error:
            logger.error(f"❌ OpenAI API error during analysis: {str(api_error)}")
            # Return a user-friendly error message instead of crashing
            return f"I encountered an issue while generating the analysis. Please try again. If the problem persists, the analysis service may be temporarily unavailable."
        
    except Exception as e:
        logger.error(f"❌ Error analyzing data with GPT: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return a user-friendly error message
        return f"I encountered an error while analyzing the data: {str(e)}. Please try again."

