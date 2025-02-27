import React, {useEffect, useState} from "react";
import {deleteModel, getModels, Model} from "@/lib/api";
import {useRouter} from "next/navigation";
import {Alert, AlertDescription} from "@/components/ui/alert";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Button} from "@/components/ui/button";

export function ModelsList() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const fetchModels = async () => {
    try {
      setLoading(true);
      const data = await getModels();
      setModels(data);
      setError(null);
    } catch {
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

  const handleView = (filePath: string) => {
    console.log('View button clicked for file:', filePath);
    const encodedUrl = encodeURIComponent(filePath);
    const viewerUrl = `/stl-view?url=${encodedUrl}`;
    console.log('Navigating to:', viewerUrl);
    router.push(viewerUrl);
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
                <Button variant="outline" onClick={() => handleView(model.file_path)}>
                  View
                </Button>
                <Button variant="destructive" onClick={() => handleDelete(model.id)}>
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
