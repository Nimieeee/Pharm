export interface TokenStreamerOptions {
    /** Base speed in milliseconds per token. Default: 25 */
    speed?: number;
    /** Callback fired when the display text updates */
    onUpdate: (text: string) => void;
    /** Callback fired when streaming is complete and the buffer is empty */
    onComplete?: (finalText: string) => void;
}

export class TokenStreamer {
    private tokenBuffer: string[] = [];
    private displayBuffer: string = '';
    private isPlaying: boolean = false;
    private isComplete: boolean = false;
    private speed: number;
    private onUpdate: (text: string) => void;
    private onComplete?: (finalText: string) => void;
    private playTimeout: ReturnType<typeof setTimeout> | null = null;
    private isStopped: boolean = false;

    constructor(options: TokenStreamerOptions) {
        this.speed = options.speed || 25;
        this.onUpdate = options.onUpdate;
        this.onComplete = options.onComplete;
    }

    /**
     * Add new tokens from the network stream to the buffer
     */
    public addTokens(tokens: string[]) {
        if (this.isStopped) return;
        this.tokenBuffer.push(...tokens);

        if (!this.isPlaying) {
            this.startPlayback();
        }
    }

    /**
     * Start the playback loop that slowly flushes the buffer to the display
     */
    private startPlayback() {
        this.isPlaying = true;

        const playNext = () => {
            if (this.isStopped) return;

            if (this.tokenBuffer.length > 0) {
                // Take 1 token from the buffer
                const chunk = this.tokenBuffer.shift() || '';
                this.displayBuffer += chunk;

                // Notify UI to render
                this.onUpdate(this.displayBuffer);

                // Variable speed rhythm based on character type
                const delay = this.calculateDelay(chunk);
                this.playTimeout = setTimeout(playNext, delay);
            } else if (this.isComplete) {
                // Buffer empty and stream marked complete
                this.isPlaying = false;
                if (this.onComplete) {
                    this.onComplete(this.displayBuffer);
                }
            } else {
                // Buffer empty but stream not done yet (network is slower than playback)
                // Wait briefly and try again
                this.playTimeout = setTimeout(playNext, 50);
            }
        };

        playNext();
    }

    /**
     * Calculates a natural reading rhythm delay
     */
    private calculateDelay(chunk: string): number {
        if (!chunk) return this.speed;

        // Check the last character of the chunk for pacing rules
        const lastChar = chunk[chunk.length - 1];

        if (/[.,!?;:]/.test(lastChar)) {
            return this.speed * 3.0;  // Pause significantly at punctuation
        }
        if (/\s/.test(lastChar)) {
            return this.speed * 0.5;  // Zip faster through spaces
        }
        if (/[A-Z]/.test(lastChar)) {
            return this.speed * 1.5;  // Slight pause on capital letters
        }

        return this.speed;
    }

    /**
     * Signal that the network stream has finished sending tokens
     */
    public markComplete() {
        this.isComplete = true;
        // If we're not playing (buffer was empty), trigger complete immediately
        if (!this.isPlaying && !this.isStopped) {
            if (this.onComplete) {
                this.onComplete(this.displayBuffer);
            }
        }
    }

    /**
     * Instantly stop the streamer and clear timeouts (for unmounting)
     */
    public stop() {
        this.isStopped = true;
        this.isPlaying = false;
        if (this.playTimeout) {
            clearTimeout(this.playTimeout);
            this.playTimeout = null;
        }
    }

    /**
     * Instantly flush the remaining buffer to display (useful for fast-forwarding or skipping)
     */
    public flush() {
        if (this.tokenBuffer.length > 0) {
            this.displayBuffer += this.tokenBuffer.join('');
            this.tokenBuffer = [];
            this.onUpdate(this.displayBuffer);
        }
        this.markComplete();
    }
}
