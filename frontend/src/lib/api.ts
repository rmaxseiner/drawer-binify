// frontend/src/lib/api.ts
import { fetchWithAuth } from './auth';

export interface ModelDimensions {
  width: number;
  depth: number;
  height: number;
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