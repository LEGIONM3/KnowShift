import { FileText, Clock } from 'lucide-react';
import { FreshnessTag } from '../shared/FreshnessTag';
import { timeAgo, truncate } from '../../utils/formatting';

/**
 * SourceCard — compact card showing one retrieved source document chunk.
 *
 * @param {{ source_name, last_verified, freshness_score, chunk_preview }} source
 */
export function SourceCard({ source }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700">
      <div className="p-1.5 bg-slate-700 rounded flex-shrink-0">
        <FileText className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <p className="text-sm font-medium text-slate-200 truncate">
            {source.source_name}
          </p>
          <FreshnessTag score={source.freshness_score} size="sm" />
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Clock className="w-3 h-3" aria-hidden="true" />
          <span>Verified {timeAgo(source.last_verified)}</span>
        </div>

        {source.chunk_preview && (
          <p className="text-xs text-slate-400 italic leading-relaxed">
            &ldquo;{truncate(source.chunk_preview, 100)}&rdquo;
          </p>
        )}
      </div>
    </div>
  );
}
