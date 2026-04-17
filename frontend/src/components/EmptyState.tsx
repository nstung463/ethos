import { useTranslation } from "react-i18next";

export default function EmptyState() {
  const { t } = useTranslation();

  return (
    <div className="px-6 py-1 text-center sm:py-2">
      <h2 className="mb-2 text-[clamp(2rem,4vw,3.5rem)] font-semibold tracking-[-0.05em] text-[var(--text-primary)]">
        {t("emptyState.title", "What can I do for you?")}
      </h2>
      <p className="mx-auto mb-2 max-w-3xl text-sm leading-6 text-[var(--text-soft)] sm:text-base">
        {t("emptyState.subtitle", "Move from idea to execution in one workspace: plan slides, draft websites, scope desktop apps, and design polished product flows without switching contexts.")}
      </p>
    </div>
  );
}
