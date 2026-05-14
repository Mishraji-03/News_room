export interface ScheduleEntry {
  id: string;
  time: string;
  title: string;
  status: 'live' | 'pending' | 'review' | 'scheduled' | 'failed';
  views?: string;
  retention?: string;
}

export const todaySchedule: ScheduleEntry[] = [
  { id:'1', time:'6:00 AM', title:'China ka AI DeepSeek V4 launch hua', status:'live', views:'4.2k views', retention:'68% retention' },
  { id:'2', time:'12:00 PM', title:'ISRO moon mission 2026 latest update', status:'live', views:'2.1k views', retention:'61% retention' },
  { id:'3', time:'5:00 PM', title:'OpenAI GPT-5 release date confirm', status:'live', views:'1.8k views', retention:'59% retention' },
  { id:'4', time:'7:00 PM', title:'Tesla FSD India launch — approved?', status:'review' },
];


export const weeklySchedule = [
  { day:'Mon', slots:['Tech News','AI Update','','Crypto'] },
  { day:'Tue', slots:['Space','','Politics','Sports'] },
  { day:'Wed', slots:['AI News','ISRO','GPT-5','Tesla'] },
  { day:'Thu', slots:['Gadgets','','Science',''] },
  { day:'Fri', slots:['Weekly Recap','','Trending','Special'] },
  { day:'Sat', slots:['','Top 5','',''] },
  { day:'Sun', slots:['','','Recap',''] },
];
