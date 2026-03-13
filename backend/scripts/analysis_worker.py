#!/usr/bin/env python3
"""
PharmGPT Data Analysis Worker
Executes Python visualization code securely and returns results as JSON.
"""

import sys
import json
import io
import base64
import traceback
from typing import Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Data science imports
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


def load_data(file_path: str) -> pd.DataFrame:
    """Load data from various file formats."""
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path_lower.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_path)
    elif file_path_lower.endswith('.json'):
        return pd.read_json(file_path)
    elif file_path_lower.endswith('.tsv'):
        return pd.read_csv(file_path, sep='\t')
    else:
        # Try CSV as default
        return pd.read_csv(file_path)


def apply_style_config(style_config: Dict[str, Any]) -> None:
    """Apply style configuration to matplotlib."""
    if not style_config:
        # Default scientific style
        sns.set_theme(style="whitegrid", palette="deep")
        return
    
    # Reset to defaults first
    plt.rcdefaults()
    
    # Apply figure background
    if 'figure_facecolor' in style_config:
        plt.rcParams['figure.facecolor'] = style_config['figure_facecolor']
    
    # Apply axes background
    if 'axes_facecolor' in style_config:
        plt.rcParams['axes.facecolor'] = style_config['axes_facecolor']
    
    # Apply font family
    if 'font_family' in style_config:
        font = style_config['font_family']
        if font.lower() in ['serif', 'times', 'times new roman']:
            plt.rcParams['font.family'] = 'serif'
        else:
            plt.rcParams['font.family'] = 'sans-serif'
    
    # Apply grid settings
    if 'grid' in style_config:
        grid_config = style_config['grid']
        if isinstance(grid_config, bool):
            plt.rcParams['axes.grid'] = grid_config
        elif isinstance(grid_config, dict):
            plt.rcParams['axes.grid'] = grid_config.get('visible', True)
            if 'style' in grid_config:
                plt.rcParams['grid.linestyle'] = grid_config['style']
            if 'alpha' in grid_config:
                plt.rcParams['grid.alpha'] = grid_config['alpha']
    
    # Apply color palette
    if 'palette' in style_config:
        palette = style_config['palette']
        if isinstance(palette, list):
            sns.set_palette(palette)
    
    # Apply text colors for dark backgrounds
    if 'figure_facecolor' in style_config:
        bg_color = style_config['figure_facecolor']
        if is_dark_color(bg_color):
            plt.rcParams['text.color'] = 'white'
            plt.rcParams['axes.labelcolor'] = 'white'
            plt.rcParams['xtick.color'] = 'white'
            plt.rcParams['ytick.color'] = 'white'
            plt.rcParams['axes.edgecolor'] = 'white'


def is_dark_color(hex_color: str) -> bool:
    """Check if a hex color is dark."""
    try:
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    except:
        return False


def calculate_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive statistics for the dataframe."""
    stats_result = {
        'shape': {'rows': df.shape[0], 'columns': df.shape[1]},
        'columns': list(df.columns),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'missing_values': df.isnull().sum().to_dict(),
        'describe': {},
        'correlations': None,
        'numeric_columns': [],
        'categorical_columns': []
    }
    
    # Identify column types
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    stats_result['numeric_columns'] = numeric_cols
    stats_result['categorical_columns'] = categorical_cols
    
    # Descriptive statistics for numeric columns
    if numeric_cols:
        describe_df = df[numeric_cols].describe()
        stats_result['describe'] = describe_df.to_dict()
        
        # Correlation matrix
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            stats_result['correlations'] = corr_matrix.to_dict()
    
    # Value counts for categorical columns (top 10)
    stats_result['categorical_summary'] = {}
    for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
        value_counts = df[col].value_counts().head(10).to_dict()
        stats_result['categorical_summary'][col] = value_counts
    
    return stats_result


def execute_plotting_code(df: pd.DataFrame, plotting_code: str) -> io.BytesIO:
    """Execute the plotting code and return the figure as bytes."""
    # Create a buffer for the output
    buf = io.BytesIO()
    
    # Create a safe execution environment
    exec_globals = {
        'df': df,
        'pd': pd,
        'np': np,
        'plt': plt,
        'sns': sns,
        'stats': stats,
        'buf': buf,
        'io': io,
        '__builtins__': {
            'range': range,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'bool': bool,
            'print': print,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'isinstance': isinstance,
            'type': type,
        }
    }
    
    # Execute the code
    exec(plotting_code, exec_globals)
    
    # If buf is still empty, try to save current figure
    if buf.tell() == 0:
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                    facecolor=plt.rcParams.get('figure.facecolor', 'white'))
    
    buf.seek(0)
    plt.close('all')
    
    return buf


def process_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process the analysis request."""
    result = {
        'image': None,
        'stats': None,
        'error': None,
        'warnings': []
    }
    
    try:
        # Extract parameters
        file_path = payload.get('file_path')
        plotting_code = payload.get('plotting_code')
        style_config = payload.get('style_config', {})
        
        if not file_path:
            raise ValueError("file_path is required")
        
        # Load data
        df = load_data(file_path)
        result['warnings'].append(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Calculate statistics
        result['stats'] = calculate_statistics(df)
        
        # Apply style configuration
        apply_style_config(style_config)
        
        # Execute plotting code if provided
        if plotting_code:
            buf = execute_plotting_code(df, plotting_code)
            image_bytes = buf.getvalue()
            result['image'] = base64.b64encode(image_bytes).decode('utf-8')
            result['warnings'].append("Plot generated successfully")
        else:
            # Generate default visualization
            result['image'] = generate_default_plot(df, style_config)
            result['warnings'].append("Generated default visualization")
        
    except Exception as e:
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()
    
    return result


def generate_default_plot(df: pd.DataFrame, style_config: Dict[str, Any]) -> str:
    """Generate a default visualization based on data types."""
    buf = io.BytesIO()
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    fig, axes = plt.subplots(1, min(2, max(1, len(numeric_cols))), 
                              figsize=(12, 5))
    
    if not isinstance(axes, np.ndarray):
        axes = [axes]
    
    if len(numeric_cols) >= 2:
        # Scatter plot of first two numeric columns
        sns.scatterplot(data=df, x=numeric_cols[0], y=numeric_cols[1], ax=axes[0])
        axes[0].set_title(f'{numeric_cols[0]} vs {numeric_cols[1]}')
        
        if len(axes) > 1:
            # Distribution of first numeric column
            sns.histplot(data=df, x=numeric_cols[0], kde=True, ax=axes[1])
            axes[1].set_title(f'Distribution of {numeric_cols[0]}')
    
    elif len(numeric_cols) == 1:
        sns.histplot(data=df, x=numeric_cols[0], kde=True, ax=axes[0])
        axes[0].set_title(f'Distribution of {numeric_cols[0]}')
    
    elif len(categorical_cols) >= 1:
        value_counts = df[categorical_cols[0]].value_counts().head(10)
        sns.barplot(x=value_counts.index, y=value_counts.values, ax=axes[0])
        axes[0].set_title(f'Top values in {categorical_cols[0]}')
        axes[0].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=plt.rcParams.get('figure.facecolor', 'white'))
    buf.seek(0)
    plt.close('all')
    
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def main():
    """Main entry point."""
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        
        if not input_data.strip():
            # Try reading from command line argument
            if len(sys.argv) > 1:
                with open(sys.argv[1], 'r') as f:
                    input_data = f.read()
            else:
                print(json.dumps({'error': 'No input provided'}))
                sys.exit(1)
        
        payload = json.loads(input_data)
        result = process_request(payload)
        
        print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        print(json.dumps({'error': f'Invalid JSON input: {str(e)}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'error': str(e), 'traceback': traceback.format_exc()}))
        sys.exit(1)


if __name__ == '__main__':
    main()
