'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { generateBin, generateBaseplate, getModels, deleteModel, type Model } from '@/lib/api';
import {ArrowLeft} from "lucide-react";
import {useRouter} from "next/navigation";

export function GenerateForm() {
  const [dimensions, setDimensions] = useState({
    width: '',
    depth: '',
    height: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleGenerate = async (type: 'bin' | 'baseplate') => {
    try {
      setLoading(true);
      setMessage(null);
      const dims = {
        width: Number(dimensions.width),
        depth: Number(dimensions.depth),
        height: Number(dimensions.height)
      };

      const response = type === 'bin'
        ? await generateBin(dims)
        : await generateBaseplate(dims);

      setMessage({ type: 'success', text: response.message });
      // Trigger models list refresh
      window.dispatchEvent(new Event('refreshModels'));
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to generate model' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Model</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <Label htmlFor="width">Width (mm)</Label>
            <Input
              id="width"
              type="number"
              value={dimensions.width}
              onChange={(e) => setDimensions({ ...dimensions, width: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="depth">Depth (mm)</Label>
            <Input
              id="depth"
              type="number"
              value={dimensions.depth}
              onChange={(e) => setDimensions({ ...dimensions, depth: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="height">Height (mm)</Label>
            <Input
              id="height"
              type="number"
              value={dimensions.height}
              onChange={(e) => setDimensions({ ...dimensions, height: e.target.value })}
            />
          </div>
        </div>
        {message && (
          <Alert variant={message.type === 'success' ? 'default' : 'destructive'} className="mb-4">
            <AlertDescription>{message.text}</AlertDescription>
          </Alert>
        )}
        <div className="flex gap-4">
          <Button
            onClick={() => handleGenerate('bin')}
            className="flex-1"
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate Bin'}
          </Button>
          <Button
            onClick={() => handleGenerate('baseplate')}
            className="flex-1"
            disabled={loading}
          >
            {loading ? 'Generating...' : 'Generate Baseplate'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function NavigationHeader() {
  const router = useRouter();

  return (
    <div className="flex justify-between items-center mb-6">
      <Button
        variant="outline"
        onClick={() => router.push('/dashboard')}
        className="flex items-center gap-2"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Dashboard
      </Button>
    </div>
  );
}


export function ModelsList() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = async () => {
    try {
      setLoading(true);
      const data = await getModels();
      setModels(data);
      setError(null);
    } catch (err) {
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
    } catch (err) {
      setError('Failed to delete model');
    }
  };

  const handleView = (filePath: string) => {
    // Open file in new window/tab
    window.open(filePath, '_blank');
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

export default function DirectGeneratePage() {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <NavigationHeader />
      <GenerateForm />
      <ModelsList />
    </div>
  );
}