'use client';

import React, { useState } from 'react';
import { NavigationHeader } from "@/components/forms/NavigationHeader";
import { DrawerCreationForm } from "@/components/forms/DrawerCreationForm";
import { DrawerGrid } from "@/components/viewers/DrawerGrid";
import { BinOptionsPanel } from "@/components/forms/BinOptionsPanel";
import { calculateDrawerGrid, generateDrawerModels, PlacedBin } from "@/lib/api";

export default function CreateDrawerPage() {
  const drawerGridRef = React.useRef<{ startBinPlacement: (bin: { id: string; width: number; depth: number; }) => void }>(null);

  const [drawerDimensions, setDrawerDimensions] = useState<{
    name: string;
    width: number;
    depth: number;
    height: number;
  } | null>(null);
  
  const [gridData, setGridData] = useState<{
    units: Array<{
      width: number;
      depth: number;
      x_offset: number;
      y_offset: number;
      is_standard: boolean;
    }>;
    gridSizeX: number;
    gridSizeY: number;
  } | null>(null);
  
  const [placedBins, setPlacedBins] = useState<PlacedBin[]>([]);
  const [isGeneratingModels, setIsGeneratingModels] = useState(false);
  const [generationSuccess, setGenerationSuccess] = useState<{
    message: string;
    modelIds: string[];
  } | null>(null);
  
  const [error, setError] = useState<string | null>(null);
  
  // Handle bin placement
  const handleSelectBin = (bin: { id: string; width: number; depth: number; }) => {
    // Create a unique ID for this bin instance
    const uniqueId = `${bin.id}-${Date.now()}`;
    
    // Use the ref to start bin placement mode in the grid component
    if (drawerGridRef.current) {
      drawerGridRef.current.startBinPlacement({
        id: uniqueId,
        width: bin.width,
        depth: bin.depth
      });
    }
  };
  
  const handlePlaceBin = (bin: any) => {
    setPlacedBins(prev => [...prev, bin]);
  };
  
  const handleRemoveBin = (binId: string) => {
    setPlacedBins(prev => prev.filter(bin => bin.id !== binId));
  };

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <NavigationHeader />
      <h1 className="text-2xl font-bold">Create Custom Drawer</h1>
      
      <DrawerCreationForm 
        onCalculate={async (dimensions) => {
          try {
            setDrawerDimensions(dimensions);
            setError(null);
            
            // API call already happens in the DrawerCreationForm component
            // The grid data will be returned from the component
            const result = await calculateDrawerGrid(dimensions);
            setGridData(result);
          } catch (err) {
            console.error("Error calculating grid:", err);
            setError("Could not calculate drawer grid layout");
          }
        }} 
      />
      
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
          {error}
        </div>
      )}
      
      {gridData && (
        <div className="grid grid-cols-1 gap-6 mt-8">
          <div className="border rounded-lg p-4 bg-white">
            <h2 className="text-xl font-semibold mb-4">Drawer Layout</h2>
            <DrawerGrid 
              ref={drawerGridRef}
              units={gridData.units}
              gridSizeX={gridData.gridSizeX}
              gridSizeY={gridData.gridSizeY}
              placedBins={placedBins}
              onPlaceBin={handlePlaceBin}
              onRemoveBin={handleRemoveBin}
            />
          </div>
          
          <BinOptionsPanel 
            gridSizeX={gridData?.gridSizeX || 0}
            gridSizeY={gridData?.gridSizeY || 0}
            maxPrintWidth={220} // From GridfinityConfig.PRINT_BED_WIDTH
            maxPrintDepth={220} // From GridfinityConfig.PRINT_BED_DEPTH
            onSelectBin={handleSelectBin}
          />
          
          {placedBins.length > 0 && (
            <div className="border rounded-lg p-4 bg-white">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Placed Bins</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPlacedBins([])}
                    className="px-3 py-1 text-sm bg-red-50 text-red-600 hover:bg-red-100 rounded"
                  >
                    Clear All
                  </button>
                  <button
                    onClick={async () => {
                      if (!drawerDimensions) return;
                      
                      try {
                        setIsGeneratingModels(true);
                        setError(null);
                        setGenerationSuccess(null);
                        
                        const result = await generateDrawerModels({
                          name: drawerDimensions.name,
                          width: drawerDimensions.width,
                          depth: drawerDimensions.depth,
                          height: drawerDimensions.height,
                          drawer_id: 0,
                          bins: placedBins
                        });
                        
                        setGenerationSuccess({
                          message: `Drawer "${drawerDimensions.name}" models generated successfully!`,
                          modelIds: result.modelIds || []
                        });
                      } catch (err) {
                        console.error("Error generating models:", err);
                        setError("Failed to generate drawer models");
                      } finally {
                        setIsGeneratingModels(false);
                      }
                    }}
                    disabled={isGeneratingModels}
                    className="px-3 py-1 text-sm bg-blue-50 text-blue-600 hover:bg-blue-100 rounded disabled:opacity-50"
                  >
                    {isGeneratingModels ? "Generating..." : "Generate Models"}
                  </button>
                </div>
              </div>
              
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Size</th>
                    <th className="px-4 py-2 text-left">Position</th>
                    <th className="px-4 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {placedBins.map((bin) => (
                    <tr key={bin.id} className="border-t">
                      <td className="px-4 py-2">{bin.id.split('-')[0]}</td>
                      <td className="px-4 py-2">{bin.width}mm × {bin.depth}mm</td>
                      <td className="px-4 py-2">({bin.x}, {bin.y})</td>
                      <td className="px-4 py-2">
                        <button
                          onClick={() => handleRemoveBin(bin.id)}
                          className="text-red-500 hover:text-red-700"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {generationSuccess && (
                <div className="mt-4 p-3 bg-green-50 text-green-700 rounded">
                  <div className="font-medium">{generationSuccess.message}</div>
                  <div className="mt-1 text-sm">Generated {generationSuccess.modelIds.length} model files. You can view them in the Models list.</div>
                </div>
              )}
              
              {error && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded">
                  {error}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}