export default function FollowUps({
  followUps,
  onClick,
}: {
  followUps: string[];
  onClick: (prompt: string) => void;
}) {
  if (followUps.length === 0) return null;

  return (
    <div className="mt-4">
      <div className="text-sm font-medium text-[var(--text-primary)]">Follow up</div>
      <div className="mt-1.5 flex flex-col text-left">
        {followUps.map((followUp, index) => (
          <div key={`${followUp}-${index}`}>
            <button
              type="button"
              onClick={() => onClick(followUp)}
              className="flex w-full items-center gap-2 bg-transparent py-1.5 text-left text-sm text-[var(--text-soft)] transition-colors hover:text-[var(--text-primary)] cursor-pointer"
              aria-label={`Follow up: ${followUp}`}
              title={followUp}
            >
              <div className="line-clamp-1">{followUp}</div>
            </button>
            {index < followUps.length - 1 ? (
              <hr className="border-[var(--border-subtle)]/60" />
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
