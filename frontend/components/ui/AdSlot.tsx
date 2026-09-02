/**
 * Clearly separated, self-contained ad placement. Disabled globally via
 * NEXT_PUBLIC_ADS_ENABLED=false (default). Never rendered adjacent to a
 * download/action button without the labeled divider below, so users can't
 * mistake an ad for part of the product flow.
 */
const ADS_ENABLED = process.env.NEXT_PUBLIC_ADS_ENABLED === "true";

export function AdSlot({ slot, className }: { slot: string; className?: string }) {
  if (!ADS_ENABLED) return null;

  return (
    <div className={className}>
      <p className="mb-1.5 text-center text-[10px] font-medium uppercase tracking-wider text-muted">
        Advertisement
      </p>
      <div
        data-ad-slot={slot}
        className="flex min-h-[90px] w-full items-center justify-center rounded-lg border border-dashed border-default bg-subtle text-xs text-muted"
      >
        Ad placeholder ({slot})
      </div>
    </div>
  );
}
