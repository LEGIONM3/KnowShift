import { Database } from 'lucide-react';

/**
 * EmptyState — centred illustration + text for when no data is available.
 *
 * @param {React.ComponentType} icon         Icon component (default Database)
 * @param {string}              title        Bold heading
 * @param {string}              description  Subtext
 * @param {React.ReactNode}     action       Optional CTA element
 */
export function EmptyState({
  icon: Icon = Database,
  title = 'No data yet',
  description = 'Upload documents to get started.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center
                    py-12 text-center space-y-4">
      <div className="p-4 bg-slate-800 rounded-full">
        <Icon className="w-8 h-8 text-slate-500" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <p className="text-slate-300 font-semibold">{title}</p>
        <p className="text-slate-500 text-sm max-w-xs">{description}</p>
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
