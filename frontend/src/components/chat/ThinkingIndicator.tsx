export function ThinkingIndicator() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-4">
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-2 w-2 rounded-full bg-gray-400 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
        <span className="text-sm text-gray-400">
          Pathfinder AI is analyzing your brief...
        </span>
      </div>
    </div>
  )
}
