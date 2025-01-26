'use client';

import { useState } from 'react';
import { DrawerDimensions, BinOptions } from '@/types';
import { fetchWithAuth } from '@/lib/auth';
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DrawerForm() {
  const [dimensions, setDimensions] = useState<DrawerDimensions>({
    name: '',
    width: 0,
    depth: 0,
    height: 0,
  });
  const [binOptions, setBinOptions] = useState<BinOptions | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const binOptionsResponse = await fetchWithAuth('/bin-options/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dimensions),
      });

      if (!binOptionsResponse.ok) {
        throw new Error('Failed to calculate bin options');
      }

      const binOptionsData = await binOptionsResponse.json();
      setBinOptions(binOptionsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Define Drawer Dimensions</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Drawer Name</Label>
                <Input
                  type="text"
                  id="name"
                  value={dimensions.name}
                  onChange={(e) => setDimensions({ ...dimensions, name: e.target.value })}
                  required
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="width">Width (mm)</Label>
                  <Input
                    type="number"
                    id="width"
                    value={dimensions.width || ''}
                    onChange={(e) => setDimensions({ ...dimensions, width: parseFloat(e.target.value) })}
                    required
                    min="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <Label htmlFor="depth">Depth (mm)</Label>
                  <Input
                    type="number"
                    id="depth"
                    value={dimensions.depth || ''}
                    onChange={(e) => setDimensions({ ...dimensions, depth: parseFloat(e.target.value) })}
                    required
                    min="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <Label htmlFor="height">Height (mm)</Label>
                  <Input
                    type="number"
                    id="height"
                    value={dimensions.height || ''}
                    onChange={(e) => setDimensions({ ...dimensions, height: parseFloat(e.target.value) })}
                    required
                    min="0"
                    step="0.1"
                  />
                </div>
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Calculating...' : 'Calculate Bin Options'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {binOptions && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Standard Bins</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {binOptions.standard_bins.map((bin, index) => (
                  <li key={index} className="p-2 bg-secondary rounded">
                    {bin.width} x {bin.depth} x {bin.height} mm
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Non-Standard Bins</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {binOptions.non_standard_bins.map((bin, index) => (
                  <li key={index} className="p-2 bg-secondary rounded">
                    {bin.width} x {bin.depth} x {bin.height} mm
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}