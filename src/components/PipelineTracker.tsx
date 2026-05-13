import { Check, Loader, Clock } from 'lucide-react';
import { pipelineSteps } from '../data/pipeline';

export default function PipelineTracker() {
  return (
    <div className="pipeline-box">
      <h3>Live pipeline — current video processing</h3>
      <div className="pipeline-steps">
        {pipelineSteps.map((step, i) => (
          <> 
            <div key={step.id} className={`pipeline-step ${step.status}`}>
              <div className="icon-wrap">
                {step.status === 'done' && <Check size={18} />}
                {step.status === 'active' && <Loader size={18} />}
                {step.status === 'pending' && <Clock size={18} />}
              </div>
              <span className="step-label">{step.label}</span>
            </div>
            {i < pipelineSteps.length - 1 && (
              <div className={`pipeline-connector ${step.status === 'done' ? 'done' : ''}`} />
            )}
          </>
        ))}
      </div>
    </div>
  );
}
