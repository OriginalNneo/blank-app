import axios from 'axios';
import { AuthResponse, LoginRequest, BudgetRequest, SOARequest, ReceiptProcessingResponse } from '@/types';

// Support both localhost and ngrok URLs
// For ngrok: Set NEXT_PUBLIC_API_URL to your ngrok URL (e.g., https://abc123.ngrok.io)
// For localhost: Leave unset or set to http://localhost:8000
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

export const budgetService = {
  generateBudget: async (data: BudgetRequest): Promise<Blob> => {
    const response = await api.post('/api/budget/generate', data, {
      responseType: 'blob',
    });
    return response.data;
  },

  previewBudget: async (data: BudgetRequest) => {
    const response = await api.post('/api/budget/preview', data);
    return response.data;
  },

  sendToTelegram: async (data: BudgetRequest) => {
    const response = await api.post('/api/budget/telegram-send', data);
    return response.data;
  },

  importExistingBudget: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/budget/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const soaService = {
  generateSOA: async (data: SOARequest): Promise<Blob> => {
    const response = await api.post('/api/soa/generate', data, {
      responseType: 'blob',
    });
    return response.data;
  },

  importExistingSOA: async (file: File): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/soa/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  previewSOA: async (data: SOARequest) => {
    const response = await api.post('/api/soa/preview', data);
    return response.data;
  },

  processReceipts: async (files: FileList): Promise<ReceiptProcessingResponse> => {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post('/api/soa/process-receipts', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  sendToTelegram: async (data: SOARequest) => {
    const response = await api.post('/api/soa/telegram-send', data);
    return response.data;
  },
};

export const minutesService = {
  generateMinutes: async (
    meetingContent: string,
    meetingTitle?: string,
    dateTime?: string,
    company?: string,
    location?: string,
    attendees?: string,
    absent?: string,
    meetingChair?: string
  ): Promise<Blob> => {
    const formData = new FormData();
    formData.append('meeting_content', meetingContent);
    if (meetingTitle) formData.append('meeting_title', meetingTitle);
    if (dateTime) formData.append('date_time', dateTime);
    if (company) formData.append('company', company);
    if (location) formData.append('location', location);
    if (attendees) formData.append('attendees', attendees);
    if (absent) formData.append('absent', absent);
    if (meetingChair) formData.append('meeting_chair', meetingChair);

    const response = await api.post('/api/minutes/generate', formData, {
      responseType: 'blob',
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  previewMinutes: async (
    meetingContent: string,
    meetingTitle?: string,
    dateTime?: string,
    company?: string,
    location?: string
  ) => {
    const formData = new FormData();
    formData.append('meeting_content', meetingContent);
    if (meetingTitle) formData.append('meeting_title', meetingTitle);
    if (dateTime) formData.append('date_time', dateTime);
    if (company) formData.append('company', company);
    if (location) formData.append('location', location);

    const response = await api.post('/api/minutes/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getMembers: async () => {
    const response = await api.get('/api/minutes/members');
    return response.data;
  },

  submitAttendance: async (date: string, attendance: Record<string, string>) => {
    const formData = new FormData();
    formData.append('date', date);
    formData.append('attendance', JSON.stringify(attendance));

    const response = await api.post('/api/minutes/attendance', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  uploadAttendanceFile: async (file: File, date: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('date', date);

    const response = await api.post('/api/minutes/attendance/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default api;