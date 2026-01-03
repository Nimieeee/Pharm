/**
 * PharmGPT Data Workbench - Mistral AI Agent Configuration
 * 
 * This module configures the AI models for the Data Analysis Workbench:
 * - Mistral Large: Logic & Coding (Node B: Coder, Node D: Analyst)
 * - Pixtral: Vision (Node A: Style Extractor)
 * 
 * @requires @langchain/mistralai >= 0.0.12
 */

import { ChatMistralAI } from "@langchain/mistralai";

// ============================================
// 1. LOGIC & CODING ENGINE (Mistral Large)
// ============================================
// Used for:
// - Node B (Coder): Generates Python/Matplotlib scripts
// - Node D (Analyst): Interprets p-values, trends, scientific analysis
//
// Why Mistral Large?
// - Top-tier reasoning capabilities
// - Excellent at generating Python logic
// - Adheres to strict syntax rules
// - Sophisticated scientific tone for analysis
export const logicModel = new ChatMistralAI({
  modelName: "mistral-large-latest",
  temperature: 0, // Strict deterministic output for code
  apiKey: process.env.MISTRAL_API_KEY,
});

// ============================================
// 2. VISION ENGINE (Pixtral)
// ============================================
// Used for:
// - Node A (Style Extractor): Analyzes uploaded images
// - Extracts colors, fonts, chart styles from reference images
//
// Why Pixtral?
// - Optimized for pixel/image analysis
// - Best for chart and visualization understanding
// - Powers the "Clone this Style" feature
export const visionModel = new ChatMistralAI({
  modelName: "pixtral-large-2411",
  temperature: 0, // Consistent style extraction
  apiKey: process.env.MISTRAL_API_KEY,
});

// ============================================
// MODEL ASSIGNMENT TYPES
// ============================================
export type WorkbenchNode = 'style_extractor' | 'coder' | 'analyst';

export const nodeModelMap: Record<WorkbenchNode, ChatMistralAI> = {
  style_extractor: visionModel, // Node A - needs to see image pixels
  coder: logicModel,            // Node B - generates Python/Matplotlib
  analyst: logicModel,          // Node D - interprets statistics
};

// ============================================
// HELPER: Get Model for Node
// ============================================
export function getModelForNode(node: WorkbenchNode): ChatMistralAI {
  return nodeModelMap[node];
}

// ============================================
// SYSTEM PROMPTS FOR EACH NODE
// ============================================
export const nodePrompts = {
  style_extractor: `You are a Style Extraction AI for scientific visualizations.
Analyze the uploaded image and extract:
1. Color palette (hex codes for primary, secondary, accent colors)
2. Font styles (serif/sans-serif, weights)
3. Chart type and layout
4. Grid and axis styling
5. Legend positioning

Output as structured JSON.`,

  coder: `You are a Python/Matplotlib Code Generator for scientific data visualization.
Generate clean, executable Python code that:
1. Uses matplotlib and seaborn for plotting
2. Follows the extracted style guidelines
3. Handles edge cases gracefully
4. Includes proper axis labels and legends
5. Uses publication-quality settings (dpi=300, tight_layout)

Output only valid Python code, no explanations.`,

  analyst: `You are a Scientific Data Analyst with expertise in pharmaceutical research.
Analyze the data and provide:
1. Statistical summary (mean, median, std, quartiles)
2. Significance testing results (p-values, confidence intervals)
3. Trend analysis and correlations
4. Key insights in scientific language
5. Recommendations for further analysis

Use a sophisticated, publication-ready tone.`,
};

// ============================================
// CONFIGURATION EXPORT
// ============================================
export const mistralConfig = {
  logicModel,
  visionModel,
  nodeModelMap,
  nodePrompts,
  getModelForNode,
};

export default mistralConfig;
