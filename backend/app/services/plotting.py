"""
Plotting Service
Generates charts and visualizations using Matplotlib/Seaborn.
Returns Base64-encoded PNG images.
"""

import io
import base64
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PlottingService:
    """
    Executes safe Python plotting code using Matplotlib/Seaborn
    and returns the result as a base64-encoded PNG image.
    """

    ALLOWED_IMPORTS = {
        'matplotlib', 'matplotlib.pyplot', 'matplotlib.figure',
        'seaborn', 'numpy', 'math',
    }

    async def generate_chart(self, code: str) -> Dict[str, Any]:
        """
        Execute plotting code and return the resulting figure as base64 PNG.
        
        The code MUST create a matplotlib figure. We capture it automatically.
        
        Args:
            code: Python code string that uses matplotlib/seaborn to create a plot.
            
        Returns:
            Dict with 'image_base64' (str) and 'status' (str).
        """
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt

        logger.info(f"📊 Generating chart from code ({len(code)} chars)")

        # Security: Basic validation
        forbidden = ['import os', 'import sys', 'subprocess', 'exec(', 'eval(', 
                      '__import__', 'open(', 'file(', 'input(', 'breakpoint',
                      'shutil', 'pathlib', 'glob', 'socket', 'requests', 'urllib']
        for term in forbidden:
            if term in code:
                logger.warning(f"⚠️ Blocked forbidden term in chart code: {term}")
                return {
                    "status": "error",
                    "error": f"Security: '{term}' is not allowed in chart code.",
                    "image_base64": None,
                }

        try:
            # Close any existing figures
            plt.close('all')

            # Create a restricted namespace for execution
            namespace = {}
            
            # Pre-import allowed modules into namespace
            import numpy as np
            namespace['np'] = np
            namespace['plt'] = plt
            
            try:
                import seaborn as sns
                namespace['sns'] = sns
            except ImportError:
                pass

            # Execute the plotting code
            exec(code, namespace)

            # Capture the current figure
            fig = plt.gcf()
            if not fig.get_axes():
                return {
                    "status": "error",
                    "error": "Code did not produce a plot. Make sure to call plt.plot(), plt.bar(), etc.",
                    "image_base64": None,
                }

            # Style it nicely
            fig.set_facecolor('#0a0a0a')
            for ax in fig.get_axes():
                ax.set_facecolor('#0a0a0a')
                ax.tick_params(colors='#999')
                ax.xaxis.label.set_color('#ccc')
                ax.yaxis.label.set_color('#ccc')
                ax.title.set_color('#fff')
                for spine in ax.spines.values():
                    spine.set_color('#333')

            fig.tight_layout()

            # Save to buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                        facecolor=fig.get_facecolor(), edgecolor='none')
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()
            plt.close('all')

            logger.info("✅ Chart generated successfully")
            return {
                "status": "success",
                "image_base64": image_base64,
                "error": None,
            }

        except Exception as e:
            plt.close('all')
            logger.error(f"❌ Chart generation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "image_base64": None,
            }
