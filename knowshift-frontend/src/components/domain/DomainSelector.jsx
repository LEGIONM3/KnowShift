import { motion } from 'framer-motion';

/** Domain definitions — source of truth for the UI */
const DOMAINS = [
  {
    id:          'medical',
    label:       'Medical',
    icon:        '🏥',
    description: 'Clinical guidelines & drug information',
    validityDays: 180,
  },
  {
    id:          'finance',
    label:       'Finance',
    icon:        '💰',
    description: 'Tax regulations & financial policies',
    validityDays: 90,
  },
  {
    id:          'ai_policy',
    label:       'AI Policy',
    icon:        '⚖️',
    description: 'AI governance & compliance frameworks',
    validityDays: 365,
  },
];

/**
 * DomainSelector — animated tab row for selecting the active domain.
 *
 * @param {string}   selected  Active domain id
 * @param {Function} onSelect  Callback(domainId: string)
 */
export function DomainSelector({ selected, onSelect }) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-500 uppercase font-semibold tracking-wider">
        Select Domain
      </p>
      <div className="flex gap-3 flex-wrap">
        {DOMAINS.map((domain) => {
          const isSelected = selected === domain.id;

          return (
            <motion.button
              key={domain.id}
              id={`domain-tab-${domain.id}`}
              role="tab"
              aria-selected={isSelected}
              onClick={() => onSelect(domain.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className={`
                relative flex items-center gap-2.5 px-5 py-3
                rounded-xl font-semibold transition-all duration-200
                border text-sm
                ${isSelected
                  ? 'bg-blue-600 border-blue-500 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:border-slate-600'
                }
              `}
            >
              <span className="text-lg" aria-hidden="true">{domain.icon}</span>
              <div className="text-left">
                <p className="leading-none">{domain.label}</p>
                <p className={`text-xs mt-0.5 ${isSelected ? 'text-blue-200' : 'text-slate-500'}`}>
                  {domain.validityDays}d validity
                </p>
              </div>

              {/* Animated ring highlight on active tab */}
              {isSelected && (
                <motion.div
                  layoutId="domain-indicator"
                  className="absolute inset-0 rounded-xl ring-2 ring-blue-400
                             ring-offset-2 ring-offset-slate-900"
                />
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
