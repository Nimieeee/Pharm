// Biomedical Prompt Generator
// Generates 1,000+ diverse biomedical research prompts programmatically

import { Mode } from '@/components/chat/ChatInput';

type SuggestionItem = { text: string; mode: Mode };

// Drug categories for prompt generation
const DRUG_CLASSES = [
    'ACE inhibitors', 'ARBs', 'Beta-blockers', 'Calcium channel blockers',
    'Diuretics', 'Statins', 'Fibrates', 'PCSK9 inhibitors',
    'SSRIs', 'SNRIs', 'TCAs', 'MAOIs', 'Atypical antipsychotics',
    'Benzodiazepines', 'Opioids', 'NSAIDs', 'Corticosteroids',
    'Antibiotics', 'Antivirals', 'Antifungals', 'Antiparasitics',
    'Chemotherapy agents', 'Immunotherapy', 'Targeted therapy',
    'Insulin', 'Oral hypoglycemics', 'GLP-1 agonists', 'SGLT2 inhibitors',
    'Anticoagulants', 'Antiplatelets', 'Thrombolytics',
    'Bronchodilators', 'Inhaled corticosteroids', 'Leukotriene modifiers',
    'PPIs', 'H2 blockers', 'Antiemetics', 'Laxatives',
    'Thyroid hormones', 'Antithyroid drugs', 'Bisphosphonates',
    'Immunosuppressants', 'Biologics', 'Monoclonal antibodies',
    'Vaccines', 'Gene therapies', 'Cell therapies'
];

const CONDITIONS = [
    'hypertension', 'diabetes mellitus', 'coronary artery disease',
    'heart failure', 'atrial fibrillation', 'stroke', 'COPD', 'asthma',
    'depression', 'anxiety disorders', 'schizophrenia', 'bipolar disorder',
    'Alzheimer\'s disease', 'Parkinson\'s disease', 'epilepsy', 'migraine',
    'rheumatoid arthritis', 'osteoarthritis', 'osteoporosis', 'gout',
    'inflammatory bowel disease', 'GERD', 'peptic ulcer disease',
    'chronic kidney disease', 'urinary tract infection', 'pneumonia',
    'tuberculosis', 'HIV/AIDS', 'hepatitis', 'malaria',
    'breast cancer', 'lung cancer', 'colorectal cancer', 'leukemia',
    'lymphoma', 'melanoma', 'prostate cancer', 'ovarian cancer'
];

const MECHANISMS = [
    'mechanism of action', 'pharmacokinetics', 'pharmacodynamics',
    'drug metabolism', 'drug interactions', 'adverse effects',
    'contraindications', 'dosing guidelines', 'therapeutic monitoring',
    'resistance mechanisms', 'structure-activity relationship',
    'bioavailability', 'half-life', 'protein binding', 'clearance'
];

const RESEARCH_TOPICS = [
    'drug discovery', 'clinical trials', 'personalized medicine',
    'pharmacogenomics', 'drug repurposing', 'biomarkers',
    'therapeutic targets', 'signal transduction', 'gene expression',
    'protein synthesis', 'cell signaling', 'immune response',
    'inflammation', 'apoptosis', 'angiogenesis', 'metastasis'
];

// Generate English prompts
export function generateEnglishPrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    // Drug interactions (100 prompts)
    CONDITIONS.forEach(condition => {
        prompts.push({
            text: `What are the common drug interactions in patients with ${condition}?`,
            mode: 'detailed'
        });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({
            text: `Explain the mechanism of action of ${drug}`,
            mode: 'detailed'
        });
        prompts.push({
            text: `What are the contraindications for ${drug}?`,
            mode: 'detailed'
        });
        prompts.push({
            text: `List potential side effects of ${drug}`,
            mode: 'detailed'
        });
    });

    // Compare drugs (50 prompts)
    for (let i = 0; i < DRUG_CLASSES.length - 1; i += 2) {
        prompts.push({
            text: `Compare ${DRUG_CLASSES[i]} vs ${DRUG_CLASSES[i+1]} in clinical practice`,
            mode: 'detailed'
        });
    }

    // Mechanism questions (100 prompts)
    MECHANISMS.forEach(mech => {
        DRUG_CLASSES.slice(0, 20).forEach(drug => {
            prompts.push({
                text: `Explain the ${mech} of ${drug}`,
                mode: 'detailed'
            });
        });
    });

    // Research prompts (100 prompts)
    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 10).forEach(condition => {
            prompts.push({
                text: `Deep research: ${topic} in ${condition}`,
                mode: 'deep_research'
            });
        });
    });

    // Clinical scenarios (100 prompts)
    CONDITIONS.forEach(condition => {
        prompts.push({
            text: `What are the current treatment guidelines for ${condition}?`,
            mode: 'detailed'
        });
        prompts.push({
            text: `Describe the pathophysiology of ${condition}`,
            mode: 'detailed'
        });
    });

    // Writing prompts (50 prompts)
    const writingStarters = [
        'Help me write a research manuscript introduction about',
        'Draft an abstract for a study on',
        'Write a literature review on',
        'Outline the structure of a clinical trial protocol for',
        'Suggest a title for a paper about'
    ];
    writingStarters.forEach(starter => {
        RESEARCH_TOPICS.slice(0, 10).forEach(topic => {
            prompts.push({ text: `${starter} ${topic}`, mode: 'detailed' });
        });
    });

    // Regulatory prompts (50 prompts)
    const regulatoryTopics = [
        'FDA approval process', 'EMA guidelines', 'clinical trial requirements',
        'adverse event reporting', 'biosimilar approval', 'orphan drug designation',
        'fast track designation', 'breakthrough therapy designation',
        'accelerated approval pathway', 'post-market surveillance'
    ];
    regulatoryTopics.forEach(topic => {
        prompts.push({ text: `Explain the ${topic} for new drugs`, mode: 'detailed' });
        prompts.push({ text: `What are the requirements for ${topic}?`, mode: 'detailed' });
    });

    // Deep research specific (100 prompts)
    const deepResearchStarters = [
        'Deep research: Current evidence for',
        'Deep research: Emerging therapies for',
        'Deep research: Long-term outcomes of',
        'Deep research: Mechanisms of resistance in',
        'Deep research: AI applications in',
        'Deep research: Biomarkers for',
        'Deep research: Clinical trial results for',
        'Deep research: Pharmacogenomics of',
        'Deep research: Drug interactions in',
        'Deep research: Treatment guidelines for'
    ];
    deepResearchStarters.forEach(starter => {
        CONDITIONS.slice(0, 10).forEach(condition => {
            prompts.push({ text: `${starter} ${condition}`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}

// Generate Spanish prompts
export function generateSpanishPrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    // Translations of key phrases
    const phrases = {
        interactions: '¿Cuáles son las interacciones farmacológicas comunes en pacientes con',
        mechanism: 'Explica el mecanismo de acción de',
        contraindications: '¿Cuáles son las contraindicaciones para',
        sideEffects: 'Enumera los posibles efectos secundarios de',
        compare: 'Compara',
        guidelines: '¿Cuáles son las guías de tratamiento actuales para',
        pathophysiology: 'Describe la fisiopatología de',
        research: 'Investigación profunda: Evidencia actual de',
        therapy: 'Investigación profunda: Terapias emergentes para',
        outcomes: 'Investigación profunda: Resultados a largo plazo de'
    };

    CONDITIONS.forEach(condition => {
        prompts.push({ text: `${phrases.interactions} ${condition}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.guidelines} ${condition}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.pathophysiology} ${condition}?`, mode: 'detailed' });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({ text: `${phrases.mechanism} ${drug}`, mode: 'detailed' });
        prompts.push({ text: `${phrases.contraindications} ${drug}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.sideEffects} ${drug}`, mode: 'detailed' });
    });

    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 15).forEach(condition => {
            prompts.push({ text: `${phrases.research} ${topic} en ${condition}`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}

// Generate French prompts
export function generateFrenchPrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    const phrases = {
        interactions: 'Quelles sont les interactions médicamenteuses courantes dans',
        mechanism: 'Expliquez le mécanisme d\'action de',
        contraindications: 'Quelles sont les contre-indications pour',
        sideEffects: 'Listez les effets secondaires potentiels de',
        guidelines: 'Quelles sont les recommandations de traitement actuelles pour',
        research: 'Recherche approfondie : Preuves actuelles pour',
        therapy: 'Recherche approfondie : Thérapies émergentes pour'
    };

    CONDITIONS.forEach(condition => {
        prompts.push({ text: `${phrases.interactions} ${condition} ?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.guidelines} ${condition} ?`, mode: 'detailed' });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({ text: `${phrases.mechanism} ${drug}`, mode: 'detailed' });
        prompts.push({ text: `${phrases.contraindications} ${drug} ?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.sideEffects} ${drug}`, mode: 'detailed' });
    });

    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 20).forEach(condition => {
            prompts.push({ text: `${phrases.research} ${topic} dans ${condition}`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}

// Generate German prompts
export function generateGermanPrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    const phrases = {
        interactions: 'Was sind die häufigsten Wechselwirkungen bei',
        mechanism: 'Erklären Sie den Wirkmechanismus von',
        contraindications: 'Was sind die Kontraindikationen für',
        sideEffects: 'Nennen Sie die möglichen Nebenwirkungen von',
        guidelines: 'Was sind die aktuellen Behandlungsrichtlinien für',
        research: 'Tiefenforschung: Aktuelle Evidenz für',
        therapy: 'Tiefenforschung: Neue Therapien für'
    };

    CONDITIONS.forEach(condition => {
        prompts.push({ text: `${phrases.interactions} ${condition}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.guidelines} ${condition}?`, mode: 'detailed' });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({ text: `${phrases.mechanism} ${drug}`, mode: 'detailed' });
        prompts.push({ text: `${phrases.contraindications} ${drug}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.sideEffects} ${drug}`, mode: 'detailed' });
    });

    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 20).forEach(condition => {
            prompts.push({ text: `${phrases.research} ${topic} bei ${condition}`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}

// Generate Portuguese prompts
export function generatePortuguesePrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    const phrases = {
        interactions: 'Quais são as interações medicamentosas comuns em',
        mechanism: 'Explique o mecanismo de ação de',
        contraindications: 'Quais são as contraindicações para',
        sideEffects: 'Liste os possíveis efeitos colaterais de',
        guidelines: 'Quais são as diretrizes de tratamento atuais para',
        research: 'Pesquisa profunda: Evidências atuais para',
        therapy: 'Pesquisa profunda: Terapias emergentes para'
    };

    CONDITIONS.forEach(condition => {
        prompts.push({ text: `${phrases.interactions} ${condition}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.guidelines} ${condition}?`, mode: 'detailed' });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({ text: `${phrases.mechanism} ${drug}`, mode: 'detailed' });
        prompts.push({ text: `${phrases.contraindications} ${drug}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.sideEffects} ${drug}`, mode: 'detailed' });
    });

    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 20).forEach(condition => {
            prompts.push({ text: `${phrases.research} ${topic} em ${condition}`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}

// Generate Chinese prompts
export function generateChinesePrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    CONDITIONS.forEach(condition => {
        prompts.push({ text: `${condition} 患者常见的药物相互作用有哪些？`, mode: 'detailed' });
        prompts.push({ text: `${condition} 的当前治疗指南是什么？`, mode: 'detailed' });
        prompts.push({ text: `描述${condition}的病理生理学`, mode: 'detailed' });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({ text: `解释${drug}的作用机制`, mode: 'detailed' });
        prompts.push({ text: `${drug}的禁忌症是什么？`, mode: 'detailed' });
        prompts.push({ text: `列出${drug}的潜在副作用`, mode: 'detailed' });
    });

    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 20).forEach(condition => {
            prompts.push({ text: `深入研究：${topic}在${condition}中的应用`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}

// Generate Italian prompts
export function generateItalianPrompts(): SuggestionItem[] {
    const prompts: SuggestionItem[] = [];

    const phrases = {
        interactions: 'Quali sono le comuni interazioni farmacologiche in',
        mechanism: 'Spiega il meccanismo d\'azione di',
        contraindications: 'Quali sono le controindicazioni per',
        sideEffects: 'Elenca i possibili effetti collaterali di',
        guidelines: 'Quali sono le linee guida di trattamento attuali per',
        research: 'Ricerca approfondita: Evidenze attuali per',
        therapy: 'Ricerca approfondita: Terapie emergenti per'
    };

    CONDITIONS.forEach(condition => {
        prompts.push({ text: `${phrases.interactions} ${condition}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.guidelines} ${condition}?`, mode: 'detailed' });
    });

    DRUG_CLASSES.forEach(drug => {
        prompts.push({ text: `${phrases.mechanism} ${drug}`, mode: 'detailed' });
        prompts.push({ text: `${phrases.contraindications} ${drug}?`, mode: 'detailed' });
        prompts.push({ text: `${phrases.sideEffects} ${drug}`, mode: 'detailed' });
    });

    RESEARCH_TOPICS.forEach(topic => {
        CONDITIONS.slice(0, 20).forEach(condition => {
            prompts.push({ text: `${phrases.research} ${topic} in ${condition}`, mode: 'deep_research' });
        });
    });

    return prompts.slice(0, 1000);
}
