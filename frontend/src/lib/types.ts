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

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}
