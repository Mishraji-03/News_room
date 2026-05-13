export interface PipelineStep {
  id: string;
  label: string;
  status: 'done' | 'active' | 'pending';
}

export const pipelineSteps: PipelineStep[] = [
  { id:'trending', label:'Trending', status:'done' },
  { id:'verified', label:'Verified', status:'done' },
  { id:'scripting', label:'Scripting', status:'active' },
  { id:'video', label:'Video', status:'pending' },
  { id:'upload', label:'Upload', status:'pending' },
];

export const pipelineFlow = [
  { nodes:['Google Trends','NewsAPI','Reddit RSS'], label:'Sources' },
  { nodes:['News Scout Agent'], label:'Detection' },
  { nodes:['Fact Checker'], label:'Verification' },
  { nodes:['Content Writer'], label:'Script' },
  { nodes:['Video Producer','Voice Agent'], label:'Production' },
  { nodes:['SEO Agent'], label:'Optimization' },
  { nodes:['Human Approval'], label:'Review' },
  { nodes:['Upload Agent'], label:'Publish' },
  { nodes:['Analytics Agent'], label:'Track' },
];

export const contentQueue = [
  {
    id:'1',
    title:'Tesla FSD India launch — approved?',
    scheduledTime:'7:00 PM',
    status:'pending' as const,
    script:'Tesla ne officially announce kiya hai ki unka Full Self-Driving (FSD) software ab India mein launch hone wala hai. Transport Ministry ne conditional approval di hai. Conditions mein Indian road data pe training aur local server pe data storage shamil hai...',
    source:'Reuters, Economic Times',
    keywords:['Tesla','FSD','India','Self Driving','Electric Vehicle'],
  },
  {
    id:'2',
    title:'Google Gemini 3.0 leaked features',
    scheduledTime:'Tomorrow 6:00 AM',
    status:'pending' as const,
    script:'Google ke upcoming Gemini 3.0 model ke features leak ho gaye hain. Naye features mein real-time video understanding, 10M token context window, aur native code execution shamil hai...',
    source:'The Verge, TechCrunch',
    keywords:['Google','Gemini','AI','LLM','Technology'],
  },
  {
    id:'3',
    title:'India vs Australia T20 World Cup preview',
    scheduledTime:'Tomorrow 12:00 PM',
    status:'pending' as const,
    script:'T20 World Cup 2026 mein India aur Australia ka blockbuster match hone wala hai. Dono teams ki playing XI, pitch report aur head-to-head record dekhte hain...',
    source:'ESPNcricinfo, ICC',
    keywords:['Cricket','T20','World Cup','India','Australia'],
  },
  {
    id:'4',
    title:'ChatGPT ab Hindi mein fluent',
    scheduledTime:'Tomorrow 5:00 PM',
    status:'approved' as const,
    script:'OpenAI ne ChatGPT ke Hindi language support mein major upgrade kiya hai. Ab ChatGPT Hindi mein bahut natural aur fluent responses deta hai...',
    source:'OpenAI Blog',
    keywords:['ChatGPT','Hindi','OpenAI','AI','Language'],
  },
];

export const uploadHistory = [
  { id:'1', title:'China ka AI DeepSeek V4 launch hua', platform:'YouTube', date:'14 May 2026, 6:00 AM', status:'published', views:'4.2k', retention:'68%' },
  { id:'2', title:'China ka AI DeepSeek V4 launch hua', platform:'Instagram', date:'14 May 2026, 6:05 AM', status:'published', views:'1.8k', retention:'—' },
  { id:'3', title:'ISRO moon mission 2026 latest update', platform:'YouTube', date:'14 May 2026, 12:00 PM', status:'published', views:'2.1k', retention:'61%' },
  { id:'4', title:'ISRO moon mission 2026 latest update', platform:'Instagram', date:'14 May 2026, 12:05 PM', status:'published', views:'980', retention:'—' },
  { id:'5', title:'OpenAI GPT-5 release date confirm', platform:'YouTube', date:'14 May 2026, 5:00 PM', status:'published', views:'1.8k', retention:'59%' },
  { id:'6', title:'OpenAI GPT-5 release date confirm', platform:'Instagram', date:'14 May 2026, 5:05 PM', status:'published', views:'720', retention:'—' },
  { id:'7', title:'Tesla FSD India launch — approved?', platform:'YouTube', date:'14 May 2026, 7:00 PM', status:'pending', views:'—', retention:'—' },
  { id:'8', title:'Nvidia RTX 5090 India price revealed', platform:'YouTube', date:'13 May 2026, 6:00 AM', status:'published', views:'6.1k', retention:'72%' },
  { id:'9', title:'BSNL 5G launch date final', platform:'YouTube', date:'13 May 2026, 12:00 PM', status:'published', views:'8.3k', retention:'74%' },
  { id:'10', title:'AI replace karega jobs? Reality check', platform:'YouTube', date:'13 May 2026, 5:00 PM', status:'published', views:'12.4k', retention:'78%' },
];
