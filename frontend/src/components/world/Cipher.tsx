import { cn } from "@/lib/utils";

/** Group ciphers and document numbers: codes are read character by character, so they get the mono face. */
export function Cipher({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("font-mono text-[0.8125rem] tracking-tight", className)}>{children}</span>;
}
