export interface ToolEntry {
  name: string;
  limit: string;
}

export interface ToolCategory {
  category: string;
  icon: string;
  tools: ToolEntry[];
}

export const freeTools: ToolCategory[] = [
  { category:'Trending Detection', icon:'trending-up', tools:[
    { name:'Google Trends', limit:'Unlimited' },
    { name:'GNews API', limit:'Unlimited' },
  ]},
  { category:'News Fetching', icon:'newspaper', tools:[
    { name:'NewsAPI.org', limit:'100 req/day free' },
    { name:'Reddit RSS', limit:'Unlimited' },
  ]},
  { category:'Fact Checking', icon:'shield-check', tools:[
    { name:'ClaimBuster', limit:'Free tier' },
    { name:'MediaBias API', limit:'Free tier' },
  ]},
  { category:'Script Writing', icon:'pen-tool', tools:[
    { name:'Gemini 1.5 Flash', limit:'1500 req/day free' },
    { name:'Claude API', limit:'Free tier' },
  ]},
  { category:'Voice Over', icon:'mic', tools:[
    { name:'Google Cloud TTS', limit:'4M chars/month free' },
    { name:'Edge TTS', limit:'Unlimited' },
  ]},
  { category:'Video Editing', icon:'video', tools:[
    { name:'FFmpeg', limit:'Completely free' },
    { name:'CapCut', limit:'Free plan' },
  ]},
  { category:'AI Anchor', icon:'user', tools:[
    { name:'D-ID', limit:'5 videos/month free' },
    { name:'HeyGen', limit:'3 videos/month free' },
  ]},
  { category:'Thumbnails', icon:'image', tools:[
    { name:'Canva Free', limit:'Unlimited' },
    { name:'Figma Free', limit:'3 projects' },
  ]},
  { category:'Upload & Schedule', icon:'upload-cloud', tools:[
    { name:'YouTube Data API v3', limit:'Free' },
    { name:'Meta Graph API', limit:'Free' },
    { name:'Buffer Free', limit:'3 channels' },
  ]},
  { category:'Analytics', icon:'bar-chart-2', tools:[
    { name:'YouTube Analytics', limit:'Free' },
    { name:'Instagram Insights', limit:'Free' },
  ]},
  { category:'Automation', icon:'zap', tools:[
    { name:'n8n (self-host)', limit:'Free' },
    { name:'Railway.app', limit:'$5 free/month' },
  ]},
  { category:'Database', icon:'database', tools:[
    { name:'Supabase PostgreSQL', limit:'500MB free' },
    { name:'Firebase', limit:'Free tier' },
  ]},
];
