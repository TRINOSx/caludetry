import clsx from 'clsx';

interface SkeletonCardProps {
  className?: string;
  lines?: number;
  showHeader?: boolean;
}

export default function SkeletonCard({
  className,
  lines = 3,
  showHeader = true,
}: SkeletonCardProps) {
  return (
    <div className={clsx('glass-panel p-4 space-y-3', className)}>
      {showHeader && (
        <div className="skeleton h-5 w-2/3 rounded" />
      )}
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton h-3 rounded"
          style={{ width: `${80 - i * 15}%` }}
        />
      ))}
    </div>
  );
}

export function SkeletonChart({ className }: { className?: string }) {
  return (
    <div className={clsx('glass-panel p-4', className)}>
      <div className="skeleton h-5 w-1/3 mb-4 rounded" />
      <div className="skeleton h-48 w-full rounded" />
    </div>
  );
}

export function SkeletonTable({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={clsx('glass-panel p-4 space-y-2', className)}>
      <div className="flex gap-4 mb-3">
        {[1, 2, 3, 4].map((c) => (
          <div key={c} className="skeleton h-4 flex-1 rounded" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {[1, 2, 3, 4].map((c) => (
            <div key={c} className="skeleton h-3 flex-1 rounded" />
          ))}
        </div>
      ))}
    </div>
  );
}
