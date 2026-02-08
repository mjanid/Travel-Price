export interface Meta {
  request_id?: string;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

export interface ApiResponse<T> {
  data: T | null;
  meta?: Meta;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
  errors?: string[];
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Trip {
  id: string;
  user_id: string;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string | null;
  travelers: number;
  trip_type: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TripCreateRequest {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  travelers?: number;
  trip_type?: string;
  notes?: string;
}

export interface TripUpdateRequest {
  origin?: string;
  destination?: string;
  departure_date?: string;
  return_date?: string | null;
  travelers?: number;
  trip_type?: string;
  notes?: string | null;
}

export interface PriceWatch {
  id: string;
  user_id: string;
  trip_id: string;
  provider: string;
  target_price: number;
  currency: string;
  is_active: boolean;
  alert_cooldown_hours: number;
  created_at: string;
  updated_at: string;
}

export interface PriceWatchCreateRequest {
  trip_id: string;
  provider?: string;
  target_price: number;
  currency?: string;
  alert_cooldown_hours?: number;
}

export interface PriceWatchUpdateRequest {
  target_price?: number;
  is_active?: boolean;
  alert_cooldown_hours?: number;
}

export interface Alert {
  id: string;
  price_watch_id: string;
  user_id: string;
  price_snapshot_id: string;
  alert_type: string;
  channel: string;
  status: string;
  target_price: number;
  triggered_price: number;
  message: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface PriceSnapshot {
  id: string;
  trip_id: string;
  provider: string;
  price: number;
  currency: string;
  cabin_class: string | null;
  airline: string | null;
  outbound_departure: string | null;
  outbound_arrival: string | null;
  return_departure: string | null;
  return_arrival: string | null;
  stops: number | null;
  scraped_at: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}
