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
    console.log('Token saved successfully:', token.slice(0, 10) + '...');
  } catch (error) {
    console.error('Error saving token:', error);
  }
}

export function getToken(): string | null {
  try {
    const token = localStorage.getItem('token');
    // Log token for debugging (only first few characters)
    if (token) {
      console.log('Retrieved token:', token.slice(0, 10) + '...');
    } else {
      console.warn('No token found in localStorage');
    }
    return token;
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
  // Basic error checking for token
  const token = getToken();
  if (!token) {
    console.error('No authentication token found');
    window.location.href = '/login';
    return Promise.reject(new Error('No authentication token'));
  }

  // Setup headers with authorization
  let requestHeaders = new Headers(options.headers);
  requestHeaders.set('Authorization', `Bearer ${token}`);
  
  // Don't override Content-Type if it's already set (for form data)
  if (!requestHeaders.has('Content-Type') && !options.body || typeof options.body === 'string') {
    requestHeaders.set('Content-Type', 'application/json');
  }

  // Prepare the URL with any necessary query parameters
  let fullUrl = `${API_URL}${url}`;
  
  // Add the local_kw parameter to prevent 422 errors
  // This parameter is required by the backend to avoid SQLAlchemy session issues
  if (!fullUrl.includes('?')) {
    fullUrl += '?local_kw=temp';
  } else if (!fullUrl.includes('local_kw=')) {
    fullUrl += '&local_kw=temp';
  }

  try {
    // Make the fetch request
    const response = await fetch(fullUrl, {
      ...options,
      headers: requestHeaders
    });

    // Handle authentication errors
    if (response.status === 401) {
      console.error('Authentication expired or invalid');
      removeToken();
      window.location.href = '/login';
      return Promise.reject(new Error('Authentication expired'));
    }

    // For successful responses, just return
    if (response.ok) {
      return response;
    }
    
    // Special handling for 422 Unprocessable Entity (validation errors)
    if (response.status === 422) {
      try {
        const errorData = await response.json();
        // Just log it but continue
        console.warn('Validation error:', errorData);
        // Return the response anyway, let the caller handle it
        return response;
      } catch (e) {
        // If we can't parse the error, just continue
        console.warn('422 error but could not parse response');
        return response;
      }
    }
    
    // Only log other errors
    if (response.status !== 422) {
      console.warn(`API Status: ${response.status} ${response.statusText}`);
    }
    
    // Return the response even if not ok, let the caller decide how to handle it
    return response;
  } catch (error) {
    // Handle network errors or other exceptions
    console.error('Network error:', error);
    return Promise.reject(new Error('Network error: Unable to connect to server'));
  }
}

// Add only the new isAuthenticated function
export function isAuthenticated(): boolean {
  const token = getToken();
  return !!token;
}
