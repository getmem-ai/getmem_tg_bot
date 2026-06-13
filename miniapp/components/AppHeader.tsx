import Image from "next/image";

interface AppHeaderProps {
  name?: string;
  tagline?: string;
}

/** Slim top brand bar — shows the generated logo mark on every screen. */
export function AppHeader({
  name = "GetMem",
  tagline = "Memory-first assistant",
}: AppHeaderProps) {
  return (
    <header className="mb-4 flex items-center gap-2.5">
      <Image
        src="/brand/logo.png"
        alt={name}
        width={34}
        height={34}
        className="rounded-xl shadow-soft"
        priority
      />
      <div className="leading-tight">
        <p className="text-[15px] font-extrabold tracking-tight text-text">
          {name}
        </p>
        <p className="text-[11px] text-muted">{tagline}</p>
      </div>
    </header>
  );
}
