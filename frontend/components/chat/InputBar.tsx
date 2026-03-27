"use client";

import { memo, useRef, useState } from "react";
import { Paperclip, SendHorizontal, Sparkles, X } from "lucide-react";

import { getRandomDemoPrompt } from "@/lib/demo-prompts";

type InputBarProps = {
  onSubmit: (message: string, file: File | null) => Promise<void> | void;
  disabled?: boolean;
};

export const InputBar = memo(function InputBar({ onSubmit, disabled = false }: InputBarProps) {
  const [message, setMessage] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canSubmit = !disabled && (message.trim().length > 0 || selectedFile !== null);

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
    <form onSubmit={handleSubmit} className="brand-panel border-t border-brand-silver px-5 py-4 sm:px-6">
      <div className="flex flex-col gap-3">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-center gap-3 text-[0.68rem] uppercase tracking-[0.24em]">
            <span className="font-mono text-brand-electric-indigo">Composer</span>
            <span className="font-mono text-brand-slate-light">chat / hr / rag</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {selectedFile ? (
              <div className="flex max-w-full items-center gap-2 border border-brand-silver bg-brand-white px-3 py-2 text-xs text-brand-midnight">
                <span className="truncate font-mono uppercase tracking-[0.16em] text-brand-slate-light">
                  {selectedFile.name}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = "";
                    }
                  }}
                  className="text-brand-slate transition-colors hover:text-brand-midnight"
                  aria-label="Remove selected file"
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ) : null}

            <button
              type="button"
              disabled={disabled}
              onClick={handleInsertDemoPrompt}
              className="inline-flex h-10 items-center gap-2 border border-brand-midnight px-3 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-midnight transition-colors hover:border-brand-electric-indigo hover:bg-brand-electric-indigo hover:text-brand-white disabled:cursor-not-allowed disabled:opacity-40"
              aria-label="Insert demo prompt"
            >
              <Sparkles className="size-3.5" />
              demo prompt
            </button>
          </div>
        </div>

        <div className="grid gap-2 md:grid-cols-[auto_1fr_auto]">
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
            className="inline-flex h-12 items-center justify-center gap-2 border border-brand-silver bg-brand-white px-4 text-brand-slate transition-colors hover:border-brand-electric-indigo hover:text-brand-midnight disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Attach file"
          >
            <Paperclip className="size-4" />
            <span className="font-mono text-[0.68rem] uppercase tracking-[0.2em]">attach</span>
          </button>

          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            disabled={disabled}
            placeholder="Write a message"
            className="h-12 w-full border border-brand-silver bg-brand-white px-4 text-sm text-brand-midnight outline-none placeholder:text-brand-slate-light focus:border-brand-electric-indigo disabled:cursor-not-allowed disabled:opacity-60"
          />

          <button
            type="submit"
            disabled={!canSubmit}
            className="inline-flex h-12 items-center justify-center gap-2 border border-brand-electric-indigo bg-brand-electric-indigo px-4 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-white transition-colors hover:bg-brand-indigo-deep disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Send message"
          >
            send
            <SendHorizontal className="size-4" />
          </button>
        </div>
      </div>
    </form>
  );
});
