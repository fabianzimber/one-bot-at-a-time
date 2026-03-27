"use client";

import { useMemo, useRef, useState } from "react";
import { Paperclip, SendHorizontal, Sparkles, X } from "lucide-react";

import { getRandomDemoPrompt } from "@/lib/demo-prompts";

type InputBarProps = {
  onSubmit: (message: string, file: File | null) => Promise<void> | void;
  disabled?: boolean;
};

export function InputBar({ onSubmit, disabled = false }: InputBarProps) {
  const [message, setMessage] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const canSubmit = useMemo(() => {
    return !disabled && (message.trim().length > 0 || selectedFile !== null);
  }, [disabled, message, selectedFile]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await onSubmit(message.trim(), selectedFile);
    setMessage("");
    setSelectedFile(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(event.target.files?.[0] ?? null);
  };

  const handleInsertDemoPrompt = () => {
    setMessage(getRandomDemoPrompt());
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full flex-col gap-2 border-t border-brand-slate p-4"
    >
      {selectedFile ? (
        <div className="flex w-fit items-center gap-2 rounded-full border border-brand-slate bg-brand-indigo-deep px-3 py-1 text-xs font-mono text-brand-ghost">
          <span className="truncate">{selectedFile.name}</span>
          <button
            type="button"
            onClick={() => {
              setSelectedFile(null);
              if (fileInputRef.current) {
                fileInputRef.current.value = "";
              }
            }}
            className="text-brand-slate-light transition-colors hover:text-brand-ghost"
            aria-label="Remove selected file"
          >
            <X className="size-3.5" />
          </button>
        </div>
      ) : null}

      <div className="flex items-center justify-between gap-3 text-[0.68rem] uppercase tracking-[0.22em] text-brand-slate-light">
        <span className="font-mono">Chat / HR / RAG demos</span>
        <button
          type="button"
          disabled={disabled}
          onClick={handleInsertDemoPrompt}
          className="inline-flex h-8 items-center gap-2 rounded-full border border-brand-slate bg-brand-midnight px-3 font-mono text-[0.68rem] tracking-[0.18em] text-brand-ghost transition-colors hover:border-brand-electric-indigo hover:text-brand-white disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Insert demo prompt"
        >
          <Sparkles className="size-3.5" />
          demo
        </button>
      </div>

      <div className="flex items-center gap-2">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          aria-label="Upload file"
        />

        <button
          type="button"
          disabled={disabled}
          onClick={() => fileInputRef.current?.click()}
          className="inline-flex size-10 items-center justify-center rounded-lg border border-brand-slate bg-brand-midnight text-brand-slate-light transition-colors hover:border-brand-electric-indigo hover:text-brand-ghost disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Attach file"
        >
          <Paperclip className="size-4" />
        </button>

        <input
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          disabled={disabled}
          placeholder="Write a message"
          className="h-10 w-full rounded-lg border border-brand-slate bg-brand-midnight px-3 text-sm text-brand-ghost outline-none placeholder:text-brand-slate-light focus:border-brand-electric-indigo disabled:cursor-not-allowed disabled:opacity-60"
        />

        <button
          type="submit"
          disabled={!canSubmit}
          className="inline-flex size-10 items-center justify-center rounded-lg border border-brand-electric-indigo bg-brand-electric-indigo text-brand-white transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Send message"
        >
          <SendHorizontal className="size-4" />
        </button>
      </div>
    </form>
  );
}
