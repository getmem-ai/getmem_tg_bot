import Image from "next/image";

/** Slim top brand bar — shows the generated logo mark on every screen. */
export function AppHeader() {
  return (
    <header className="mb-4 flex items-center gap-2.5">
      <Image
        src="/brand/logo.png"
        alt="GetMem"
        width={34}
        height={34}
        className="rounded-xl shadow-soft"
        priority
      />
      <div className="leading-tight">
        <p className="text-[15px] font-extrabold tracking-tight text-text">
          GetMem
        </p>
        <p className="text-[11px] text-muted">Memory-first assistant</p>
      </div>
    </header>
  );
}
