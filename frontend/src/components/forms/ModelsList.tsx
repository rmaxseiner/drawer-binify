import React, {useEffect, useState} from "react";
import {deleteModel, getModels, Model} from "@/lib/api";
import {useRouter} from "next/navigation";
import {Alert, AlertDescription} from "@/components/ui/alert";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Button} from "@/components/ui/button";
import { FileType, Cube3D } from "lucide-react";

export function ModelsList() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const fetchModels = async () => {
    try {
      setLoading(true);
      const data = await getModels();
      
      // Debug the models data
      console.log('Models fetched:', data);
      
      // Check if there are any models with missing file paths
      const modelsWithMissingPaths = data.filter(model => !model.file_path);
      if (modelsWithMissingPaths.length > 0) {
        console.warn('Models with missing file paths:', modelsWithMissingPaths);
      }
      
      setModels(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching models:', err);
      setError('Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
    window.addEventListener('refreshModels', fetchModels);
    return () => window.removeEventListener('refreshModels', fetchModels);
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteModel(id);
      await fetchModels();
    } catch {
      setError('Failed to delete model');
    }
  };

  const handleView = (model: Model) => {
    console.log('View button clicked for model:', model);
    
    // If we have a specific file path, use it
    if (model.file_path) {
      const encodedUrl = encodeURIComponent(model.file_path);
      const viewerUrl = `/stl-view?url=${encodedUrl}`;
      console.log('Navigating to:', viewerUrl);
      router.push(viewerUrl);
    } else {
      // Otherwise use the direct API endpoint that will find the STL file for the model ID
      // Use full absolute URL instead of relative path
      const apiUrl = `http://localhost:8000/models/view/${model.id}/stl`;
      console.log('Creating STL viewer URL for model:', model.id);
      const viewerUrl = `/stl-view?url=${encodeURIComponent(apiUrl)}`;
      console.log('Navigating to:', viewerUrl);
      router.push(viewerUrl);
    }
  };
  

  if (loading) return <div className="text-center p-4">Loading...</div>;
  if (error) return <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generated Models</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {models.map((model) => (
            <div key={`${model.type}-${model.id}`} className="flex items-center justify-between p-4 border rounded">
              <div>
                <div className="font-medium">{model.name}</div>
                <div className="text-sm text-gray-500">
                  {model.type} • {new Date(model.date_created).toLocaleDateString()}
                </div>
                <div className="text-sm text-gray-500">
                  {model.width} x {model.depth} x {model.height} mm
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleView(model)}>
                  <Cube3D className="h-4 w-4 mr-1" />
                  View STL
                </Button>
                <Button variant="outline" size="sm" onClick={() => window.open(`/api/models/view/${model.id}/cad`, '_blank')}>
                  <FileType className="h-4 w-4 mr-1" />
                  Download CAD
                </Button>
                <Button variant="destructive" size="sm" onClick={() => handleDelete(model.id)}>
                  Delete
                </Button>
              </div>
            </div>
          ))}
          {models.length === 0 && (
            <div className="text-center text-gray-500">No models generated yet</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
