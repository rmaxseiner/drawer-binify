import React, {useState} from "react";
import {generateBaseplate, generateBin} from "@/lib/api";
import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";
import {Label} from "@/components/ui/label";
import {Input} from "@/components/ui/input";
import {Alert, AlertDescription} from "@/components/ui/alert";
import {Button} from "@/components/ui/button";

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
    } catch {
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