import { Mode } from '@/components/chat/ChatInput';
import { LanguageCode } from '@/lib/translations';

type SuggestionItem = { text: string; mode: Mode };

const SUGGESTIONS_EN: SuggestionItem[] = [
    // --- Clinical Pharmacology & Therapeutics ---
    { text: 'What are the common drug interactions with Warfarin?', mode: 'detailed' },
    { text: 'Explain the mechanism of action of SSRIs', mode: 'detailed' },
    { text: 'Compare ACE inhibitors vs ARBs in treating hypertension', mode: 'detailed' },
    { text: 'List potential side effects of GLP-1 agonists', mode: 'detailed' },
    { text: 'Analyze the structure-activity relationship of beta-lactams', mode: 'detailed' },
    { text: 'What are the contraindications for tissue plasminogen activator (tPA)?', mode: 'detailed' },
    { text: 'Discuss the pharmacokinetics of therapeutic monoclonal antibodies', mode: 'detailed' },
    { text: 'Explain the CYP450 enzyme inhibition profile of ritonavir', mode: 'detailed' },
    { text: 'What are the current treatment guidelines for H. pylori infection?', mode: 'detailed' },
    { text: 'Describe the mechanism of resistance to vancomycin in S. aureus', mode: 'detailed' },

    // --- Research, Writing & Academic ---
    { text: 'Help me write a research manuscript introduction', mode: 'detailed' },
    { text: 'Draft an abstract for a study on mRNA vaccine stability', mode: 'detailed' },
    { text: 'Write a literature review on antibiotic resistance mechanisms', mode: 'detailed' },
    { text: 'Suggest a title for a paper on AI in drug discovery', mode: 'detailed' },
    { text: 'Outline the structure of a Phase I clinical trial protocol', mode: 'detailed' },

    // --- Regulatory Affairs & Industry ---
    { text: 'Summarize the latest FDA guidelines for biosimilars', mode: 'detailed' },
    { text: 'What are phase III trial requirements for orphan drugs?', mode: 'detailed' },
    { text: 'Explain the Fast Track designation process by the FDA', mode: 'detailed' },
    { text: 'What are the reporting requirements for adverse events (post-market)?', mode: 'detailed' },
    { text: 'Compare FDA vs EMA approval processes for new molecular entities', mode: 'detailed' },

    // --- Deep Research Queries ---
    { text: 'Deep research: Current evidence for pembrolizumab in NSCLC', mode: 'deep_research' },
    { text: 'Deep research: Emerging CAR-T therapies for solid tumors', mode: 'deep_research' },
    { text: 'Deep research: Long-term outcomes of gene therapy in hemophilia', mode: 'deep_research' },
    { text: 'Deep research: AI applications in drug discovery 2024', mode: 'deep_research' },
    { text: 'Deep research: Mechanisms of resistance to EGFR tyrosine kinase inhibitors', mode: 'deep_research' },
];

const SUGGESTIONS_ES: SuggestionItem[] = [
    // --- Clinical Pharmacology & Therapeutics (Spanish) ---
    { text: '¿Cuáles son las interacciones farmacológicas comunes con la warfarina?', mode: 'detailed' },
    { text: 'Explica el mecanismo de acción de los ISRS', mode: 'detailed' },
    { text: 'Compara los inhibidores de la ECA vs ARA II en el tratamiento de la hipertensión', mode: 'detailed' },
    { text: 'Enumera los posibles efectos secundarios de los agonistas GLP-1', mode: 'detailed' },
    { text: 'Analiza la relación estructura-actividad de los betalactámicos', mode: 'detailed' },

    // --- Research, Writing & Academic (Spanish) ---
    { text: 'Ayúdame a escribir la introducción de un manuscrito de investigación', mode: 'detailed' },
    { text: 'Redacta un resumen para un estudio sobre la estabilidad de vacunas de ARNm', mode: 'detailed' },
    { text: 'Escribe una revisión bibliográfica sobre mecanismos de resistencia a antibióticos', mode: 'detailed' },

    // --- Deep Research (Spanish) ---
    { text: 'Investigación profunda: Evidencia actual de pembrolizumab en NSCLC', mode: 'deep_research' },
    { text: 'Investigación profunda: Terapias CAR-T emergentes para tumores sólidos', mode: 'deep_research' },
];

const SUGGESTIONS_FR: SuggestionItem[] = [
    // --- Clinical Pharmacology & Therapeutics (French) ---
    { text: 'Quelles sont les interactions médicamenteuses courantes avec la warfarine ?', mode: 'detailed' },
    { text: 'Expliquez le mécanisme d\'action des ISRS', mode: 'detailed' },
    { text: 'Comparez les inhibiteurs de l\'ECA et les ARA II dans le traitement de l\'hypertension', mode: 'detailed' },
    { text: 'Listez les effets secondaires potentiels des agonistes du GLP-1', mode: 'detailed' },

    // --- Research, Writing & Academic (French) ---
    { text: 'Aidez-moi à rédiger une introduction de manuscrit de recherche', mode: 'detailed' },
    { text: 'Rédigez un résumé pour une étude sur la stabilité des vaccins à ARNm', mode: 'detailed' },

    // --- Deep Research (French) ---
    { text: 'Recherche approfondie : Preuves actuelles pour le pembrolizumab dans le CBNPC', mode: 'deep_research' },
    { text: 'Recherche approfondie : Thérapies CAR-T émergentes pour les tumeurs solides', mode: 'deep_research' },
];

// Fallback to EN if specific language not fully populated yet
const SUGGESTIONS_DE: SuggestionItem[] = [
    { text: 'Was sind die häufigsten Wechselwirkungen mit Warfarin?', mode: 'detailed' },
    { text: 'Erklären Sie den Wirkmechanismus von SSRIs', mode: 'detailed' },
    { text: 'Vergleichen Sie ACE-Hemmer vs. ARBs bei der Behandlung von Bluthochdruck', mode: 'detailed' },
];

export const getSuggestionPool = (language: LanguageCode = 'en'): SuggestionItem[] => {
    switch (language) {
        case 'es': return SUGGESTIONS_ES;
        case 'fr': return SUGGESTIONS_FR;
        case 'de': return SUGGESTIONS_DE;
        case 'en':
        default:
            return SUGGESTIONS_EN;
    }
};

// Deprecated: For backward compatibility if needed, but should act as "default"
export const SUGGESTION_POOL = SUGGESTIONS_EN;
