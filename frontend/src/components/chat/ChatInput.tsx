'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, Loader2, Zap, BookOpen, Search, Send, Square,
  Paperclip, FileText, File, Table, XCircle, X, Mic, MicOff
} from 'lucide-react';
import { toast } from 'sonner';
import { useSidebar } from '@/contexts/SidebarContext';

export type Mode = 'fast' | 'detailed' | 'deep_research';

interface ChatInputProps {
  onSend: (message: string, mode: Mode) => void;
  onStop?: () => void;
  onFileUpload?: (files: FileList) => Promise<any>;
  onCancelUpload?: () => void;
  onRemoveFile?: (fileName: string) => void;
  isLoading: boolean;
  isUploading?: boolean;
  mode: Mode;
  setMode: (mode: Mode) => void;
}

interface Attachment {
  id: string;
  file: File;
  status: 'uploading' | 'ready' | 'error';
  error?: string;
}

const modes: { id: Mode; label: string; icon: typeof Zap; desc: string }[] = [
  { id: 'fast', label: 'Fast', icon: Zap, desc: 'Quick answers' },
  { id: 'detailed', label: 'Detailed', icon: BookOpen, desc: 'Comprehensive' },
  { id: 'deep_research', label: 'Deep Research', icon: Search, desc: 'PubMed literature review' },
];

export default function ChatInput({ onSend, onStop, onFileUpload, onCancelUpload, onRemoveFile, isLoading, isUploading = false, mode, setMode }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Refs for click-outside detection
  const desktopMenuRef = useRef<HTMLDivElement>(null);
  const desktopBtnRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const mobileBtnRef = useRef<HTMLButtonElement>(null);

  // Handle click outside to close attach menu
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!showAttachMenu) return;
      const target = event.target as Node;

      const isDesktop = desktopMenuRef.current?.contains(target) || desktopBtnRef.current?.contains(target);
      const isMobile = mobileMenuRef.current?.contains(target) || mobileBtnRef.current?.contains(target);

      if (!isDesktop && !isMobile) {
        setShowAttachMenu(false);
      }
    };

    if (showAttachMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showAttachMenu]);

  const { sidebarOpen } = useSidebar();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processFiles(e.target.files);
      e.target.value = ''; // Reset input
    }
    setShowAttachMenu(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await processFiles(e.dataTransfer.files);
    }
  };

  const processFiles = async (files: FileList) => {
    if (!onFileUpload) return;

    // 1. Validation: Max 5 files at once
    if (files.length > 5) {
      alert("You can only upload up to 5 files at a time.");
      return;
    }

    // 2. Validation: Max 20MB per file
    const MAX_SIZE = 20 * 1024 * 1024; // 20MB
    const validFiles: File[] = [];

    Array.from(files).forEach(file => {
      if (file.size > MAX_SIZE) {
        alert(`File '${file.name}' exceeds the 20MB limit.`);
      } else {
        validFiles.push(file);
      }
    });

    if (validFiles.length === 0) return;

    // Create temporary attachments
    const newAttachments: Attachment[] = validFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      status: 'uploading'
    }));

    setAttachments(prev => [...prev, ...newAttachments]);

    // Create FileList from valid files
    const dt = new DataTransfer();
    validFiles.forEach(file => dt.items.add(file));
    const filteredFileList = dt.files;

    // Upload files
    try {
      const results = await onFileUpload(filteredFileList);

      // Update status based on results
      setAttachments(prev => prev.map(att => {
        const result = results?.find((r: any) => r.fileName === att.file.name);
        if (result) {
          return {
            ...att,
            status: result.status,
            error: result.error
          };
        }
        // If not found in results (shouldn't happen if logic matches), keep as is or mark error
        return att;
      }));
    } catch (error) {
      console.error("Upload error", error);
      // Mark all new attachments as error if the whole call failed
      setAttachments(prev => prev.map(att =>
        newAttachments.find(na => na.id === att.id)
          ? { ...att, status: 'error', error: 'Upload failed' }
          : att
      ));
    }
  };

  const removeAttachment = (id: string) => {
    const attachment = attachments.find(a => a.id === id);
    if (attachment) {
      // Call the new removeFile function if provided
      if (onRemoveFile) {
        onRemoveFile(attachment.file.name);
      }
      // Fallback for backward compatibility or if no specific removal logic needed on backend
      // (but we added logic to backend/hook so we should rely on it)
    }
    setAttachments(prev => prev.filter(a => a.id !== id));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim(), mode);
      setMessage('');
      setAttachments([]); // Clear attachments on send
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
  };

  // Audio recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        await transcribeAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.info('Recording... Click again to stop');
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Could not access microphone. Please allow microphone access.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsTranscribing(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');

      const token = localStorage.getItem('auth_token');
      let apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      // Ensure HTTPS to prevent Mixed Content errors
      if (apiUrl.startsWith('http://')) {
        apiUrl = apiUrl.replace('http://', 'https://');
      }

      const response = await fetch(`${apiUrl}/api/v1/audio/transcribe`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (data.success && data.text) {
        setMessage(prev => prev ? `${prev} ${data.text}` : data.text);
        toast.success('Transcription complete');
        // Focus textarea
        textareaRef.current?.focus();
      } else {
        toast.error(data.error || 'Transcription failed');
      }
    } catch (error) {
      console.error('Transcription error:', error);
      toast.error('Failed to transcribe audio');
    } finally {
      setIsTranscribing(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const currentMode = modes.find(m => m.id === mode)!;

  // Helper to get file icon and color
  const getFileVisuals = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') return { color: 'bg-red-500', icon: FileText };
    if (['doc', 'docx'].includes(ext || '')) return { color: 'bg-blue-500', icon: File };
    if (['xls', 'xlsx', 'csv'].includes(ext || '')) return { color: 'bg-green-500', icon: Table };
    return { color: 'bg-gray-500', icon: File };
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.pptx,.sdf,.mol,.png,.jpg,.jpeg,.gif,.bmp,.webp"
        multiple
        onChange={handleFileChange}
      />

      {/* Gradient Fade Mask - Desktop */}
      <div
        className="hidden md:block fixed bottom-0 right-0 h-32 pointer-events-none z-30 bg-gradient-to-t from-[var(--background)] to-transparent transition-all duration-300"
        style={{ left: sidebarOpen ? '280px' : '0' }}
      />

      {/* Desktop Floating Capsule */}
      <div
        className="hidden md:block fixed bottom-8 z-[40] w-[60%] min-w-[500px] max-w-[700px] transition-all duration-300"
        style={{
          left: sidebarOpen ? 'calc(140px + 50%)' : '50%',
          transform: 'translateX(-50%)'
        }}
      >
        {/* Action Chips Floating Above */}
        <div className="flex items-center justify-center gap-2 mb-3">
          {modes.map((m) => {
            const Icon = m.icon;
            const isActive = mode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 border
                  ${isActive
                    ? 'bg-[var(--surface)] border-[var(--accent)] text-[var(--accent)] shadow-sm scale-105'
                    : 'bg-[var(--surface)]/80 border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface)] hover:text-[var(--text-primary)] backdrop-blur-sm'
                  }
                `}
              >
                <Icon size={12} strokeWidth={2} />
                {m.label}
              </button>
            );
          })}
        </div>

        <form onSubmit={handleSubmit}>
          <div
            className={`relative rounded-[28px] border-2 transition-all ${isDragging
              ? 'border-[var(--accent)] bg-[var(--accent)]/5'
              : 'border-[var(--border)] hover:border-[var(--text-secondary)]/30'
              } bg-[var(--surface)] shadow-2xl flex flex-col`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
          >
            {/* File Attachment Grid */}
            <AnimatePresence>
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-2 px-4 pt-4 pb-1">
                  {attachments.map((att) => {
                    const { color, icon: Icon } = getFileVisuals(att.file.name);
                    return (
                      <motion.div
                        key={att.id}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className={`flex items-center gap-3 p-2 pr-3 bg-[var(--surface)] border rounded-xl shadow-sm ${att.status === 'error' ? 'border-red-500/50' : 'border-[var(--border)]'
                          }`}
                      >
                        {/* Icon Box */}
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white ${color} relative overflow-hidden`}>
                          {att.status === 'uploading' ? (
                            <Loader2 size={20} className="animate-spin" />
                          ) : (
                            <Icon size={20} />
                          )}
                        </div>

                        {/* Text Info */}
                        <div className="flex flex-col min-w-[80px]">
                          <span className="text-xs font-bold text-[var(--text-primary)] truncate max-w-[120px]">
                            {att.file.name}
                          </span>
                          <span className="text-[10px] text-[var(--text-secondary)]">
                            {att.status === 'error' ? 'Failed' : formatSize(att.file.size)}
                          </span>
                        </div>

                        {/* Remove Button */}
                        <button
                          type="button"
                          onClick={() => removeAttachment(att.id)}
                          className="ml-1 text-[var(--text-secondary)] hover:text-red-500 transition-colors"
                        >
                          <XCircle size={16} />
                        </button>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </AnimatePresence>



            <div className="relative w-full">
              {/* Left: Plus Button (Attach Menu) */}
              <div className="absolute left-3 top-1/2 -translate-y-1/2 z-[51]">
                <div className="relative">
                  <button
                    ref={desktopBtnRef}
                    type="button"
                    onClick={() => setShowAttachMenu(!showAttachMenu)}
                    disabled={isUploading}
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isUploading
                      ? 'bg-[var(--accent)]/20 cursor-not-allowed'
                      : 'bg-[var(--surface-highlight)] hover:bg-[var(--border)]'
                      }`}
                  >
                    {isUploading ? (
                      <Loader2 size={18} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
                    ) : (
                      <Plus
                        size={20}
                        strokeWidth={2}
                        className={`text-[var(--text-secondary)] transition-transform duration-200 ease-out ${showAttachMenu ? 'rotate-45' : 'rotate-0'}`}
                      />
                    )}
                  </button>

                  {/* Attach Menu Dropdown - Desktop (Upload Only) */}
                  <AnimatePresence>
                    {showAttachMenu && (
                      <motion.div
                        ref={desktopMenuRef}
                        initial={{ opacity: 0, scale: 0, originX: 0, originY: 1 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0, transition: { duration: 0.2, ease: "backIn" } }}
                        className="absolute bottom-full left-0 mb-4 w-56 p-2 rounded-3xl bg-[var(--surface)] border border-[var(--border)] shadow-2xl z-[50] overflow-hidden"
                      >
                        <button
                          type="button"
                          onClick={() => { fileInputRef.current?.click(); setShowAttachMenu(false); }}
                          className="w-full flex items-center gap-3 p-3 rounded-xl text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50 transition-colors"
                        >
                          <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
                            <Paperclip size={16} strokeWidth={1.5} className="text-[var(--accent)]" />
                          </div>
                          <div className="text-left">
                            <span className="text-sm font-medium block">Upload File</span>
                            <span className="text-[10px] text-[var(--text-secondary)]">PDF, DOCX, CSV, Images</span>
                          </div>
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Center: Text Input */}
              <textarea
                ref={textareaRef}
                value={message}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder={`Ask anything in ${currentMode.label} mode...`}
                disabled={isLoading}
                rows={1}
                className="w-full py-[18px] pl-16 pr-28 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] resize-none focus:outline-none text-base"
                style={{ minHeight: '60px', maxHeight: '200px' }}
              />

              {/* Right: Mic + Send/Stop Buttons */}
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 z-10">
                {/* Microphone Button */}
                <motion.button
                  type="button"
                  onClick={toggleRecording}
                  disabled={isLoading || isTranscribing}
                  whileTap={{ scale: 0.95 }}
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${isRecording
                    ? 'bg-red-500 text-white animate-pulse'
                    : isTranscribing
                      ? 'bg-[var(--surface-highlight)] text-[var(--accent)]'
                      : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  title={isRecording ? 'Stop recording' : isTranscribing ? 'Transcribing...' : 'Voice input'}
                >
                  {isTranscribing ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : isRecording ? (
                    <MicOff size={18} />
                  ) : (
                    <Mic size={18} />
                  )}
                </motion.button>

                {/* Send/Stop Button */}
                {isLoading ? (
                  <motion.button
                    type="button"
                    onClick={onStop}
                    whileTap={{ scale: 0.95 }}
                    className="w-10 h-10 rounded-full flex items-center justify-center bg-red-500 text-white hover:bg-red-600 transition-all"
                    title="Stop generating"
                  >
                    <Square size={14} fill="currentColor" />
                  </motion.button>
                ) : (
                  <motion.button
                    type="submit"
                    disabled={!message.trim() || isUploading}
                    whileTap={{ scale: 0.95 }}
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${message.trim() && !isUploading
                      ? 'bg-[var(--foreground)] text-[var(--background)]'
                      : 'bg-[var(--surface-highlight)] text-[var(--text-secondary)]'
                      }`}
                  >
                    <Send size={18} strokeWidth={2} />
                  </motion.button>
                )}
              </div>
            </div>
          </div>

          <div className="text-center mt-2">
            <p className="text-[10px] text-[var(--text-secondary)]">
              PharmGPT can make mistakes. Consider checking important information.
            </p>
          </div>
        </form>
      </div>

      {/* Mobile Floating Capsule - ChatGPT Style */}
      <div className="md:hidden fixed bottom-4 left-4 right-4 z-[40]">
        <div className="fixed bottom-0 left-0 right-0 h-24 pointer-events-none -z-10 bg-gradient-to-t from-[var(--background)] to-transparent" />

        <form onSubmit={handleSubmit}>
          <div className={`relative rounded-[24px] border-2 transition-all ${isDragging
            ? 'border-[var(--accent)] bg-[var(--accent)]/5'
            : 'border-[var(--border)]'
            } bg-[var(--surface)] dark:bg-[#1E1E1E] shadow-xl flex flex-col`}>

            {/* Mobile File Attachment Grid */}
            <AnimatePresence>
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-2 px-3 pt-3 pb-1">
                  {attachments.map((att) => {
                    const { color, icon: Icon } = getFileVisuals(att.file.name);
                    return (
                      <motion.div
                        key={att.id}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className={`flex items-center gap-2 p-1.5 pr-2 bg-[var(--surface)] border rounded-lg shadow-sm ${att.status === 'error' ? 'border-red-500/50' : 'border-[var(--border)]'
                          }`}
                      >
                        <div className={`w-8 h-8 rounded-md flex items-center justify-center text-white ${color}`}>
                          {att.status === 'uploading' ? (
                            <Loader2 size={14} className="animate-spin" />
                          ) : (
                            <Icon size={14} />
                          )}
                        </div>
                        <div className="flex flex-col min-w-[60px]">
                          <span className="text-[10px] font-bold text-[var(--text-primary)] truncate max-w-[80px]">
                            {att.file.name}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => removeAttachment(att.id)}
                          className="ml-1 text-[var(--text-secondary)] hover:text-red-500"
                        >
                          <XCircle size={14} />
                        </button>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </AnimatePresence>

            <div className="relative w-full">
              {/* Left: Plus Button */}
              <div className="absolute left-1.5 top-1/2 -translate-y-1/2 z-[51]">
                <div className="relative">
                  <button
                    ref={mobileBtnRef}
                    type="button"
                    onClick={() => setShowAttachMenu(!showAttachMenu)}
                    disabled={isUploading}
                    className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${isUploading
                      ? 'bg-[var(--accent)]/20 cursor-not-allowed'
                      : 'bg-[var(--surface-highlight)] dark:bg-[#2A2A2A]'
                      }`}
                  >
                    {isUploading ? (
                      <Loader2 size={16} strokeWidth={1.5} className="text-[var(--accent)] animate-spin" />
                    ) : (
                      <Plus
                        size={18}
                        strokeWidth={2}
                        className={`text-[var(--text-secondary)] transition-transform duration-200 ease-out ${showAttachMenu ? 'rotate-45' : 'rotate-0'}`}
                      />
                    )}
                  </button>

                  <AnimatePresence>
                    {showAttachMenu && (
                      <motion.div
                        ref={mobileMenuRef}
                        initial={{ opacity: 0, scale: 0, originX: 0, originY: 1 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0, transition: { duration: 0.2, ease: "backIn" } }}
                        className="absolute bottom-full left-0 mb-4 w-64 p-2 rounded-3xl bg-[var(--surface)] border border-[var(--border)] shadow-2xl z-[50] overflow-hidden"
                      >
                        <button
                          type="button"
                          onClick={() => { fileInputRef.current?.click(); setShowAttachMenu(false); }}
                          className="w-full flex items-center gap-3 p-3 rounded-xl text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50 transition-colors"
                        >
                          <div className="w-8 h-8 rounded-lg bg-[var(--accent)]/10 flex items-center justify-center">
                            <Paperclip size={16} strokeWidth={1.5} className="text-[var(--accent)]" />
                          </div>
                          <div className="text-left">
                            <span className="text-sm font-medium block">Upload File</span>
                            <span className="text-[10px] text-[var(--text-secondary)]">PDF, DOCX, CSV, Images</span>
                          </div>
                        </button>

                        <div className="h-px bg-[var(--border)]/50 my-1 mx-2" />

                        {modes.map((m) => {
                          const Icon = m.icon;
                          const isActive = mode === m.id;
                          return (
                            <button
                              key={m.id}
                              type="button"
                              onClick={() => { setMode(m.id); setShowAttachMenu(false); }}
                              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-colors ${isActive
                                ? 'bg-[var(--accent)]/10 text-[var(--accent)]'
                                : 'text-[var(--text-primary)] hover:bg-[var(--surface-highlight)]/50'
                                }`}
                            >
                              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isActive ? 'bg-[var(--accent)]/20' : 'bg-[var(--surface-highlight)]'
                                }`}>
                                <Icon size={16} strokeWidth={1.5} />
                              </div>
                              <div className="text-left">
                                <p className="text-sm font-medium">{m.label}</p>
                                <p className="text-[10px] text-[var(--text-secondary)]">{m.desc}</p>
                              </div>
                            </button>
                          );
                        })}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              {/* Center: Text Input */}
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Message..."
                disabled={isLoading}
                className="w-full py-3 pl-12 pr-12 bg-transparent text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none text-sm text-center"
              />

              {/* Right: Send/Stop Button */}
              <div className="absolute right-1.5 top-1/2 -translate-y-1/2 flex items-center z-10">
                {isLoading ? (
                  <motion.button
                    type="button"
                    onClick={onStop}
                    whileTap={{ scale: 0.95 }}
                    className="w-9 h-9 rounded-full flex items-center justify-center bg-red-500 text-white hover:bg-red-600 transition-all"
                    title="Stop generating"
                  >
                    <Square size={12} fill="currentColor" />
                  </motion.button>
                ) : (
                  <motion.button
                    type="submit"
                    disabled={!message.trim() || isUploading}
                    whileTap={{ scale: 0.95 }}
                    className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${message.trim() && !isUploading
                      ? 'bg-[var(--text-primary)] text-[var(--background)]'
                      : 'bg-transparent text-[var(--text-secondary)]'
                      }`}
                  >
                    <Send size={14} strokeWidth={2} />
                  </motion.button>
                )}
              </div>
            </div>
          </div>
        </form>
      </div>
    </>
  );
}
