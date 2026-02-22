export interface StreamHandlers<T = any> {
    onContent: (content: string) => void;
    onMeta?: (meta: any) => void;
    onDone?: () => void;
    onError?: (error: Error) => void;
    // Custom parser if the stream doesn't send standard text/JSON data events
    customParser?: (data: string) => void;
}

/**
 * Standard Server-Sent Events (SSE) stream processor
 */
export async function processSSEStream(
    response: Response,
    handlers: StreamHandlers
): Promise<void> {
    if (!response.body) {
        throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';
    let buffer = '';
    let isDone = false;
    let lineCount = 0;

    console.log('🔄 Stream reader initialized');

    try {
        while (!isDone) {
            const { done, value } = await reader.read();
            
            if (done) {
                console.log(`📭 Stream ended naturally (${lineCount} lines processed)`);
                break;
            }

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                lineCount++;
                
                if (line.startsWith('data: ')) {
                    const data = line.slice(6).trim();

                    if (data === '[DONE]') {
                        console.log('🏁 Received [DONE] signal');
                        isDone = true;
                        break;
                    }

                    if (handlers.customParser) {
                        handlers.customParser(data);
                        continue;
                    }

                    // Handle Meta events
                    if (data.includes('"user_message_id"') || data.startsWith('{"type": "meta"')) {
                        try {
                            const meta = JSON.parse(data);
                            handlers.onMeta?.(meta);
                        } catch (e) {
                            console.error('Failed to parse meta event:', e);
                        }
                        continue;
                    }

                    // Skip random JSON logs
                    if (data.startsWith('{') && (data.includes('"timestamp"') || data.includes('"level"'))) {
                        continue;
                    }

                    // Parse text chunk
                    let textContent = '';
                    try {
                        const parsed = JSON.parse(data);
                        textContent = parsed.text !== undefined ? parsed.text : data.replace(/\\n/g, '\n');
                    } catch {
                        textContent = data.replace(/\\n/g, '\n');
                    }

                    fullContent += textContent;
                    handlers.onContent(fullContent);
                }
            }
        }

        // Process leftover buffer
        if (buffer.startsWith('data: ')) {
            const data = buffer.slice(6).trim();
            if (data !== '[DONE]') {
                if (handlers.customParser) {
                    handlers.customParser(data);
                } else {
                    let textContent = '';
                    try {
                        const parsed = JSON.parse(data);
                        textContent = parsed.text !== undefined ? parsed.text : data.replace(/\\n/g, '\n');
                    } catch {
                        textContent = data.replace(/\\n/g, '\n');
                    }
                    fullContent += textContent;
                    handlers.onContent(fullContent);
                }
            }
        }

        console.log('✅ Calling onDone handler');
        handlers.onDone?.();

    } catch (error: any) {
        if (error.name === 'AbortError') {
            console.log('⚠️ Stream aborted');
        } else {
            console.error('❌ Stream error:', error);
            handlers.onError?.(error);
            throw error;
        }
    }
}
