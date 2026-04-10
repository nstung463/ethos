export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1" aria-label="Assistant is typing">
      <span className="typing-dot" />
      <span className="typing-dot" style={{ animationDelay: "0.18s" }} />
      <span className="typing-dot" style={{ animationDelay: "0.36s" }} />
    </div>
  );
}
