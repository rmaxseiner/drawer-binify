import { LoginCredentials, AuthResponse } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);
  formData.append('grant_type', 'password');  // Add this line

  const url = `${API_URL}/token`;
  console.log('Login attempt:', {
    url,
    username: credentials.username,
    apiUrl: API_URL
  });

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      },
      body: formData,
      credentials: 'include',  // Add this line
      mode: 'cors',           // Add this line
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Login failed:', response.status, errorData);
      throw new Error(`Login failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('Login successful, received data:', data);
    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}

export function setToken(token: string) {
  try {
    localStorage.setItem('token', token);
    console.log('Token saved successfully');
  } catch (error) {
    console.error('Error saving token:', error);
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem('token');
  } catch (error) {
    console.error('Error getting token:', error);
    return null;
  }
}

export function removeToken() {
  localStorage.removeItem('token');
}


// Update the existing fetchWithAuth function in src/lib/auth.ts
export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getToken();
  if (!token) {
    window.location.href = '/login';
    throw new Error('No authentication token');
  }

  const headers = {
    ...options.headers,
    Authorization: `Bearer ${token}`,
  };

  const response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    removeToken();
    window.location.href = '/login';
    throw new Error('Authentication expired');
  }

  return response;
}

// Add only the new isAuthenticated function
export function isAuthenticated(): boolean {
  const token = getToken();
  return !!token;
}
