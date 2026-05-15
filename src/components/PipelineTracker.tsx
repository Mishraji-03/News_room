import { memo } from 'react';
import { Check, Loader2, Clock, AlertCircle } from 'lucide-react';

// ============================================================
// TYPES
// ============================================================

export type StepStatus = 'pending' | 'active' | 'done' | 'error';

export interface PipelineStep {
  id: string;
  label: string;
  status?: StepStatus;
}

export interface PipelineTrackerProps {
  currentTask: string;
  runId?: string | null;
  steps?: PipelineStep[];
  errorStep?: string | null;
  className?: string;
}

const DEFAULT_STEPS: PipelineStep[] = [
  { id: 'scrape', label: 'Scraping' },
  { id: 'fact', label: 'Fact Checking' },
  { id: 'script', label: 'Writing' },
  { id: 'video', label: 'Rendering' },
  { id: 'upload', label: 'Uploading' },
];

function getActiveIndexFromTask(currentTask: string, steps: PipelineStep[]): number {
  const taskLower = currentTask.toLowerCase();
  if (taskLower.includes('scraping')) return 0;
  if (taskLower.includes('fact check')) return 1;
  if (taskLower.includes('script')) return 2;
  if (taskLower.includes('video') || taskLower.includes('rendering')) return 3;
  if (taskLower.includes('upload') || taskLower.includes('publishing') || taskLower.includes('queue')) return 4;
  if (taskLower.includes('finished') || taskLower.includes('completed')) return steps.length - 1;
  return -1;
}

const PipelineTracker = memo(function PipelineTracker({
  currentTask,
  runId,
  steps = DEFAULT_STEPS,
  errorStep = null,
  className = '',
}: PipelineTrackerProps) {
  const activeIndex = getActiveIndexFromTask(currentTask, steps);

  const stepsWithStatus = steps.map((step, idx) => {
    let status: StepStatus = 'pending';
    if (errorStep === step.id) status = 'error';
    else if (idx < activeIndex) status = 'done';
    else if (idx === activeIndex) status = 'active';
    return { ...step, status };
  });

  return (
    <div className={`mt-8 ${className}`}>
      <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-3xl p-6 backdrop-blur-sm shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="text-sm font-bold text-zinc-100 uppercase tracking-widest flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Live Pipeline
            </h3>
            <p className="text-xs text-zinc-500 mt-1">{currentTask}</p>
          </div>
          <div className="text-[10px] font-mono text-zinc-600 bg-zinc-950 px-2 py-1 rounded border border-zinc-900">
            {runId ? `ID: ${runId.slice(-8).toUpperCase()}` : 'ID: —'}
          </div>
        </div>

        {/* Steps Flow */}
        <div className="relative flex items-center justify-between w-full">
          {/* Background Connector Line */}
          <div className="absolute top-5 left-0 right-0 h-0.5 bg-zinc-800 -z-0" />
          
          {/* Active Progress Line */}
          <div 
            className="absolute top-5 left-0 h-0.5 bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-700 ease-in-out -z-0"
            style={{ width: `${(Math.max(0, activeIndex) / (steps.length - 1)) * 100}%` }}
          />

          {stepsWithStatus.map((step, idx) => {
            const isActive = step.status === 'active';
            const isDone = step.status === 'done';
            const isError = step.status === 'error';

            return (
              <div key={step.id} className="relative z-10 flex flex-col items-center">
                {/* Circle */}
                <div 
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center
                    transition-all duration-300 border-2
                    ${isDone ? 'bg-emerald-500 border-emerald-500 text-zinc-950 shadow-[0_0_15px_rgba(16,185,129,0.3)]' : ''}
                    ${isActive ? 'bg-zinc-950 border-emerald-500 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.5)]' : ''}
                    ${isError ? 'bg-red-500 border-red-500 text-white' : ''}
                    ${!isDone && !isActive && !isError ? 'bg-zinc-950 border-zinc-800 text-zinc-600' : ''}
                  `}
                >
                  {isDone && <Check size={20} strokeWidth={3} />}
                  {isActive && <Loader2 size={20} className="animate-spin" />}
                  {isError && <AlertCircle size={20} />}
                  {!isDone && !isActive && !isError && <span className="text-xs font-bold">{idx + 1}</span>}
                </div>

                {/* Label */}
                <span 
                  className={`
                    absolute -bottom-7 whitespace-nowrap text-[10px] font-bold uppercase tracking-tighter
                    transition-colors duration-300
                    ${isActive ? 'text-emerald-400' : isDone ? 'text-zinc-300' : 'text-zinc-600'}
                  `}
                >
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>

        {/* Bottom Status Message */}
        <div className="mt-14 flex items-center gap-3 px-4 py-3 bg-zinc-950/50 rounded-xl border border-zinc-800/50">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-xs text-zinc-400 font-medium italic">
            {activeIndex === steps.length - 1 ? 'Pipeline execution finalized successfully.' : `Orchestrating ${currentTask}...`}
          </span>
        </div>
      </div>
    </div>
  );
});

export default PipelineTracker;