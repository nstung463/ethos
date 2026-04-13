export default function EmptyState() {
  return (
    <div className="px-6 py-4 text-center sm:py-5">
      <h2 className="mb-4 text-[clamp(2.2rem,5vw,4.3rem)] font-semibold tracking-[-0.05em] text-[var(--text-primary)]">
        What can I do for you?
      </h2>
      <p className="mx-auto mb-8 max-w-3xl text-sm leading-7 text-[var(--text-soft)] sm:text-base">
        Move from idea to execution in one workspace: plan slides, draft websites, scope desktop apps, and design polished
        product flows without switching contexts.
      </p>
    </div>
  );
}
