import pandas as pd
import io

def process_spreadsheet(content: bytes, ext: str, user_prompt: str):
    """
    Smart Data Analysis: Provides a summary and structure for the LLM.
    """
    try:
        if ext == 'csv':
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
            
        # Generate a "Data Profile"
        columns = ", ".join(df.columns.tolist())
        row_count = len(df)
        
        # Get basic stats
        description = df.describe(include='all').to_markdown()
        
        # Get a sample
        head_sample = df.head(10).to_markdown()

        # We return a formatted string. 
        # The Main Chat LLM will use this context to answer the user's prompt.
        return (
            f"# Data File Analysis\n"
            f"**User Instruction:** {user_prompt}\n\n"
            f"**Metadata:** {row_count} rows, Columns: [{columns}]\n\n"
            f"## Statistical Summary\n{description}\n\n"
            f"## Data Preview (First 10 rows)\n{head_sample}"
        )
    except Exception as e:
        return f"Error reading data file: {e}"
