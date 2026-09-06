// Admin Dashboard API Types

export interface WidgetConfig {
  welcome_message: string;
  quick_replies: string[];
  bot_name?: string;
  bot_avatar?: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatReference {
  title: string;
  source: string;
  score: number;
  content?: string;
}

export interface ChatResponse {
  reply: string;
  session_id: string;
  references: ChatReference[];
}

export interface SSESessionEvent {
  type: 'session';
  session_id: string;
}

export interface SSEChunkEvent {
  type: 'chunk';
  content: string;
}

export interface SSEDoneEvent {
  type: 'done';
  references: Omit<ChatReference, 'content'>[];
}

export interface SSEErrorEvent {
  type: 'error';
  message: string;
}

export type SSEEvent = SSESessionEvent | SSEChunkEvent | SSEDoneEvent | SSEErrorEvent;

// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    name: string;
    email: string;
    role: string;
  };
  detail?: string; // for error responses
}

// Users
export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: 'Super Admin' | 'CS Agent' | 'Editor (Knowledge Base)';
  status: string;
  last_active: string;
  created_at: string;
}

export interface UserCreateRequest {
  name: string;
  email: string;
  password: string;
  role: 'Super Admin' | 'CS Agent' | 'Editor (Knowledge Base)';
}

// Stats
export interface KPIStats {
  total_conversations: number;
  active_users: number;
  unanswered_queries: number;
}

export interface ChartDataPoint {
  name: string;
  chats: number;
  percakapan: number;
  unresolved: number;
}

export interface AnalyticsMetrics {
  avg_response_time: string;
  active_users_30min: number;
  monthly_active: number;
}

export interface AdminStatsResponse {
  kpi: KPIStats;
  chart: ChartDataPoint[];
  metrics: AnalyticsMetrics;
}

// Conversations
export interface ChatSession {
  session_id: string;
  last_message: string;
  created_at: string;
  updated_at: string;
}

export interface SessionHistory {
  session_id: string;
  history: Message[];
  is_human_handoff: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  role: 'user' | 'assistant' | 'admin' | 'system';
  content: string;
  timestamp?: number;
}

// Unanswered
export interface UnansweredQuery {
  id: number;
  session_id?: string;
  user_query: string;
  query?: string; // alias for backward compat
  created_at: string;
}

// Knowledge Base
export interface KBFile {
  filename: string;
  size: number;
}

// Settings
export interface Settings {
  welcome_message: string;
  quick_replies: string[];
  system_prompt: string;
}

// Admin actions
export interface AdminReplyReq {
  session_id: string;
  content: string;
}