import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface DrawerDimensions {
  name: string;
  width: number;
  depth: number;
  height: number;
}

interface DrawerCreationFormProps {
  onCalculate: (dimensions: DrawerDimensions) => void;
}

export function DrawerCreationForm({ onCalculate }: DrawerCreationFormProps) {
  const [drawerInfo, setDrawerInfo] = useState({
    name: "",
    width: "",
    depth: "",
    height: ""
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setDrawerInfo(prev => ({ ...prev, [id]: value }));
  };

  const handleCalculate = async () => {
    // Basic validation
    if (!drawerInfo.name.trim()) {
      setError("Please provide a drawer name");
      return;
    }

    const width = parseFloat(drawerInfo.width);
    const depth = parseFloat(drawerInfo.depth);
    const height = parseFloat(drawerInfo.height);

    if (isNaN(width) || width <= 0) {
      setError("Please provide a valid width");
      return;
    }

    if (isNaN(depth) || depth <= 0) {
      setError("Please provide a valid depth");
      return;
    }

    if (isNaN(height) || height <= 0) {
      setError("Please provide a valid height");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // This will later make an API call to get grid data
      const dimensions: DrawerDimensions = {
        name: drawerInfo.name,
        width,
        depth,
        height
      };
      
      // Pass the drawer dimensions to parent component for API call
      onCalculate(dimensions);
    } catch (err) {
      console.error("Error calculating drawer grid:", err);
      setError("Failed to calculate drawer layout");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Drawer Information</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <Label htmlFor="name">Drawer Name</Label>
            <Input
              id="name"
              value={drawerInfo.name}
              onChange={handleInputChange}
              placeholder="Kitchen Drawer 1"
            />
          </div>
          <div>
            <Label htmlFor="width">Width (mm)</Label>
            <Input
              id="width"
              type="number"
              value={drawerInfo.width}
              onChange={handleInputChange}
              placeholder="210"
            />
          </div>
          <div>
            <Label htmlFor="depth">Depth (mm)</Label>
            <Input
              id="depth"
              type="number"
              value={drawerInfo.depth}
              onChange={handleInputChange}
              placeholder="420"
            />
          </div>
          <div>
            <Label htmlFor="height">Height (mm)</Label>
            <Input
              id="height"
              type="number"
              value={drawerInfo.height}
              onChange={handleInputChange}
              placeholder="60"
            />
          </div>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="flex justify-end">
          <Button
            onClick={handleCalculate}
            disabled={loading}
          >
            {loading ? "Calculating..." : "Calculate Bin Options"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}