// frontend/src/lib/api.ts
import { fetchWithAuth } from './auth';

export interface ModelDimensions {
  width: number;
  depth: number;
  height: number;
}

export interface DrawerDimensions extends ModelDimensions {
  name: string;
}

export interface Model {
  id: string;
  type: string;
  name: string;
  date_created: string;
  width: number;
  depth: number;
  height: number;
  file_path: string;
}

export interface Unit {
  width: number;
  depth: number;
  x_offset: number;
  y_offset: number;
  is_standard: boolean;
}

export interface DrawerGridResponse {
  units: Unit[];
  gridSizeX: number;
  gridSizeY: number;
}

export async function generateBin(dimensions: ModelDimensions) {
  const response = await fetchWithAuth('/generate/bin/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dimensions),
  });
  return response.json();
}

export async function generateBaseplate(dimensions: ModelDimensions) {
  const response = await fetchWithAuth('/generate/baseplate/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dimensions),
  });
  return response.json();
}

export async function getModels() {
  const response = await fetchWithAuth('/models/');
  return response.json();
}

export async function deleteModel(modelId: string) {
  const response = await fetchWithAuth(`/models/${modelId}`, {
    method: 'DELETE',
  });
  return response.json();
}

export interface PlacedBin {
  id: string;
  width: number;
  depth: number;
  x: number;
  y: number;
  unitX: number;
  unitY: number;
  unitWidth: number;
  unitDepth: number;
}

export interface GenerateDrawerModelsRequest {
  name: string;
  width: number;
  depth: number;
  height: number;
  bins: PlacedBin[];
}

export async function generateDrawerModels(data: GenerateDrawerModelsRequest) {
  const response = await fetchWithAuth('/drawers/generate-models/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed to generate drawer models: ${text}`);
  }
  
  return response.json();
}

export async function calculateDrawerGrid(dimensions: DrawerDimensions): Promise<DrawerGridResponse> {
  try {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const token = localStorage.getItem('token');
    
    if (!token) {
      throw new Error('Authentication required');
    }
    
    const response = await fetch(`${API_URL}/drawers/grid-layout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(dimensions),
    });

    if (!response.ok) {
      const text = await response.text();
      try {
        const errorJson = JSON.parse(text);
        throw new Error(`Failed to calculate drawer grid: ${JSON.stringify(errorJson.detail || errorJson)}`);
      } catch (e) {
        throw new Error(`Failed to calculate drawer grid: ${text}`);
      }
    }

    return await response.json();
  } catch (error) {
    console.error("Error in calculateDrawerGrid:", error);
    throw error;
  }
}