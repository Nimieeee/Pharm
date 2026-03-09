import { Mode } from '@/components/chat/ChatInput';
import { LanguageCode } from '@/lib/translations';
import {
    generateEnglishPrompts,
    generateSpanishPrompts,
    generateFrenchPrompts,
    generateGermanPrompts,
    generatePortuguesePrompts,
    generateChinesePrompts,
    generateItalianPrompts
} from './prompts/promptGenerator';

type SuggestionItem = { text: string; mode: Mode };

// Cache for generated prompts (lazy loading)
let cachedPrompts: Record<string, SuggestionItem[]> = {};

function getPromptsForLanguage(language: LanguageCode): SuggestionItem[] {
    if (!cachedPrompts[language]) {
        switch (language) {
            case 'en':
                cachedPrompts['en'] = generateEnglishPrompts();
                break;
            case 'es':
                cachedPrompts['es'] = generateSpanishPrompts();
                break;
            case 'fr':
                cachedPrompts['fr'] = generateFrenchPrompts();
                break;
            case 'de':
                cachedPrompts['de'] = generateGermanPrompts();
                break;
            case 'pt':
                cachedPrompts['pt'] = generatePortuguesePrompts();
                break;
            case 'zh':
                cachedPrompts['zh'] = generateChinesePrompts();
                break;
            case 'it':
                cachedPrompts['it'] = generateItalianPrompts();
                break;
            default:
                cachedPrompts['en'] = generateEnglishPrompts();
        }
    }
    return cachedPrompts[language];
}

export const getSuggestionPool = (language: LanguageCode = 'en'): SuggestionItem[] => {
    return getPromptsForLanguage(language);
};

// Legacy export for backward compatibility
export const SUGGESTION_POOL = getPromptsForLanguage('en');
