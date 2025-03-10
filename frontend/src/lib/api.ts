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

export async function getUserInfo() {
  try {
    // Check if token exists
    const token = localStorage.getItem('token');
    if (!token) {
      return {
        username: 'Guest',
        email: '',
        first_name: '',
        last_name: ''
      };
    }

    console.log('Using token to get user info...');
    
    // Make the real API request
    const response = await fetchWithAuth('/users/me/');
    
    if (!response.ok) {
      throw new Error(`Failed to get user info: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching user info:', error);
    // Return default user to prevent UI errors
    return {
      username: 'Guest',
      email: '',
      first_name: '',
      last_name: ''
    };
  }
}

export async function getUserDrawers() {
  try {
    console.log('Fetching user drawers from API...');
    
    // Make the actual API request
    const response = await fetchWithAuth('/drawers/');
    
    if (!response.ok) {
      throw new Error(`Failed to get user drawers: ${response.status}`);
    }
    
    const drawers = await response.json();
    console.log('Retrieved drawers:', drawers);
    return drawers;
  } catch (error) {
    console.error('Error fetching user drawers:', error);
    // Return empty array instead of throwing
    return [];
  }
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
  // Log the request data for debugging
  console.log('Generating drawer models with data:', data);
  
  try {
    // Ensure all bins have valid x and y coordinates
    const validatedData = {
      ...data,
      bins: data.bins.map(bin => {
        // If x or y is null, undefined, or not a number, set to 0
        return {
          ...bin,
          x: bin.x != null ? bin.x : 0,
          y: bin.y != null ? bin.y : 0,
          // Ensure unitX and unitY are numbers and not null/undefined
          unitX: bin.unitX != null ? bin.unitX : 0,
          unitY: bin.unitY != null ? bin.unitY : 0,
        };
      })
    };
    
    const jsonData = JSON.stringify(validatedData);
    console.log('Request JSON after validation:', jsonData);
    
    const response = await fetchWithAuth('/drawers/generate-models/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonData,
    });
    
    if (!response.ok) {
      // Try to parse error as JSON first
      const text = await response.text();
      console.error('Failed to generate drawer models:', {
        status: response.status,
        statusText: response.statusText,
        responseBody: text
      });
      
      // Try to parse as JSON to provide more detailed error information
      try {
        const errorData = JSON.parse(text);
        throw new Error(`Failed to generate drawer models: ${JSON.stringify(errorData)}`);
      } catch (parseError) {
        // If parsing fails, use the raw text
        throw new Error(`Failed to generate drawer models: ${text}`);
      }
    }
    
    const result = await response.json();
    console.log('Model generation success:', result);
    return result;
  } catch (error) {
    console.error('Exception in generateDrawerModels:', error);
    throw error;
  }
}

export async function calculateDrawerGrid(dimensions: DrawerDimensions): Promise<DrawerGridResponse> {
  try {
    const response = await fetchWithAuth('/drawers/grid-layout/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
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

export async function deleteDrawer(drawerId: number): Promise<{ message: string }> {
  try {
    const response = await fetchWithAuth(`/drawers/${drawerId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Failed to delete drawer: ${text}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error deleting drawer:", error);
    throw error;
  }
}

export async function getDrawer(drawerId: number) {
  try {
    const response = await fetchWithAuth(`/drawers/${drawerId}`);

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Failed to get drawer: ${text}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error getting drawer:", error);
    throw error;
  }
}

export async function updateDrawer(drawerId: number, drawerData: DrawerDimensions) {
  try {
    const response = await fetchWithAuth(`/drawers/${drawerId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(drawerData),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Failed to update drawer: ${text}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error updating drawer:", error);
    throw error;
  }
}

export async function updateDrawerBins(drawerId: number, bins: PlacedBin[]) {
  try {
    // Convert the frontend bin format to the expected backend format
    const backendBinFormat = bins.map(bin => ({
      width: bin.width,
      depth: bin.depth,
      x_position: bin.x,
      y_position: bin.y,
      // ID might be in format "bin-1x2-12345", so we extract just the identifier part
      // If ID is numeric, use it as is; otherwise, set it to null to create a new bin
      id: bin.id && !bin.id.includes('-') && !isNaN(Number(bin.id)) ? Number(bin.id) : null
    }));

    const response = await fetchWithAuth(`/drawers/${drawerId}/bins`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ bins: backendBinFormat }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Failed to update drawer bins: ${text}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error updating drawer bins:", error);
    throw error;
  }
}