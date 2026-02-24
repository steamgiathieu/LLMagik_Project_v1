// src/types/index.ts

export interface ApiError {
  status: number;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}
