# Mini App design system

A modern, soft, **violet-branded** mobile UI. Surfaces & text follow the
Telegram theme (light/dark adaptive); the **accent is a constant brand violet**
for a cohesive look. Inspired by premium finance/journaling app UIs: large
rounded cards, generous consistent spacing, soft diffuse shadows, pill
segmented controls, donut/area charts, a polished bottom tab bar.

## Tokens (Tailwind)
- **Brand:** `brand` ramp (`brand-50…900`, DEFAULT `#7c5cfc`, `brand-fg` white).
  Use `bg-brand`, `text-brand`, `bg-brand/10` tints, `bg-brand` gradient
  (`bg-brand` / `bg-brand-soft` background-images) for hero headers & primary CTAs.
- **Surfaces/text:** `bg-tg-bg`, `text-tg-text`, `text-tg-hint`,
  `bg-tg-secondary` (never hardcode black/white for content).
- **Radius:** `rounded-card` (20px) for cards, `rounded-card-lg` (28px) for hero
  blocks, `rounded-2xl`/`rounded-full` for chips/pills/avatars.
- **Shadow:** `shadow-soft` (chips/inputs), `shadow-card` (cards), `shadow-pop`
  (FAB / floating CTA, brand-tinted), `shadow-ring` (focus/selected halo).

## Spacing scale (use consistently)
- Screen padding: `px-4`, top `pt-5`, bottom `pb-tabbar`.
- Between sections: `gap-6` (labelled `Section`s) / cards in a list: `gap-3`.
- Inside a card: `p-5` (default), `p-4` (compact rows). Card title → body: `mt-3`.
- Icon chips: `h-10 w-10 rounded-2xl` with a tinted bg (`bg-brand/10`, brand icon).
- Pills/badges: `px-2.5 py-1 rounded-full text-xs font-semibold`.

## Components
- **Card:** `bg-tg-bg rounded-card shadow-card p-5` with a hairline border
  `border border-black/[0.04] dark:border-white/[0.06]`.
- **Primary button:** `bg-brand text-brand-fg rounded-2xl font-semibold shadow-pop`
  (active scale-[.99]); secondary: `bg-tg-secondary text-tg-text`.
- **SegmentedControl:** track `bg-tg-secondary rounded-full p-1`; active pill
  `bg-tg-bg shadow-soft` (or `bg-brand text-brand-fg` for strong emphasis).
- **Toggle:** on = `bg-brand`.
- **Stat tile:** small `text-tg-hint` label, big `text-2xl font-bold` value,
  delta in `text-emerald-500` / `text-red-500`.
- **Ring/donut (UsageRing):** thick rounded arc, brand stroke on a faint track,
  big centered value — like the reference donut.
- **Area chart (UsageChart/analytics):** smooth `monotone` line with a soft
  brand gradient fill, minimal axes, rounded dot on the active point.
- **Tab bar:** `bg-tg-bg/95 backdrop-blur` top hairline, icon+label, active =
  `text-brand`; safe-area aware.
- **Hero (Home profile):** a `bg-brand` gradient header card with white text +
  avatar, like the budget app's "My Budget" header.

## Brand assets (in `public/brand/`)
- `logo.png` — app mark (header, loading, OpenInTelegram).
- `empty.png` — empty-state illustration.

## Rules
- Reuse the tokens; don't invent ad-hoc radii/shadows/margins.
- Keep all component **props/behaviour/data contracts** unchanged — this is a
  visual system, not a logic change.
- Theme-safe: works in light and dark Telegram themes (test both).
