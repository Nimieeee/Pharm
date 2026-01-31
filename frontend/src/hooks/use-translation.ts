
import { useAuth } from '@/lib/auth-context';
import { translations, LanguageCode } from '@/lib/translations';

export function useTranslation() {
    const { user } = useAuth();

    // Default to English if no user or no language set
    const language = (user?.language || 'en') as LanguageCode;

    // Fallback to English if language code not found in dictionary, though it should be
    const dict = translations[language] || translations['en'];

    const t = (key: string): string => {
        return dict[key] || key;
    };

    return { t, language };
}
