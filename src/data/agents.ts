export interface Agent {
  id: string;
  title: string;
  role: string;
  description: string;
  tools: string[];
  color: string;
  icon: string;
}

export const agents: Agent[] = [
  { id:'ceo', title:'Manager / CEO', role:'Orchestrator', description:'Orchestrate all agents · Monitor KPIs · Final decisions', tools:['Claude Opus 4','n8n'], color:'var(--green)', icon:'crown' },
  { id:'lead', title:'Team Leader', role:'Supervisor', description:'Supervise pipeline · Quality checks · Priority queue', tools:['LangChain','AutoGPT'], color:'var(--blue)', icon:'shield' },
  { id:'hr', title:'HR Agent', role:'People Ops', description:'Log agent activity · Error handling · Daily reports', tools:['Notion AI','Slack Bot'], color:'var(--amber)', icon:'users' },
  { id:'scout', title:'News Scout', role:'Researcher', description:'Detect trending · Collect headlines · Virality score', tools:['NewsAPI','Google Trends','Reddit RSS'], color:'var(--purple)', icon:'search' },
  { id:'fact', title:'Fact Checker', role:'Tester / QA', description:'Filter fake news · Verify sources · Flag unreliable', tools:['ClaimBuster','MediaBias API'], color:'var(--orange)', icon:'shield-check' },
  { id:'writer', title:'Content Writer', role:'Backend', description:'Summarize news · Write scripts · Generate captions', tools:['Claude API','Gemini Flash'], color:'var(--green)', icon:'pen-tool' },
  { id:'video', title:'Video Producer', role:'Frontend', description:'Animated anchor · Voice-over · Shorts/Reels edit', tools:['D-ID','Pictory','CapCut'], color:'var(--red)', icon:'video' },
  { id:'seo', title:'SEO Agent', role:'Growth', description:'Keyword research · Optimize titles · Write descriptions', tools:['TubeBuddy','VidIQ','ChatGPT'], color:'var(--blue)', icon:'trending-up' },
  { id:'upload', title:'Upload Agent', role:'DevOps', description:'Auto-upload videos · Post to Instagram · Schedule', tools:['YouTube API','Meta Graph API','Buffer'], color:'var(--green)', icon:'upload-cloud' },
  { id:'analytics', title:'Analytics Agent', role:'Operations', description:'Track performance · Weekly reports · Optimize strategy', tools:['YT Analytics','Instagram Insights'], color:'var(--amber)', icon:'bar-chart-2' },
];
