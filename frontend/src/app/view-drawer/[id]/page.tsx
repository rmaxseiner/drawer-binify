'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { NavigationHeader } from "@/components/forms/NavigationHeader";
import { DrawerGrid } from "@/components/viewers/DrawerGrid";
import { BinOptionsPanel } from "@/components/forms/BinOptionsPanel";
import { getDrawer, PlacedBin, generateDrawerModels, calculateDrawerGrid, updateDrawerBins, getDrawerBaseplates } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

import {id} from "postcss-selector-parser";

export default function ViewDrawerPage() {
  const params = useParams();
  const drawerId = typeof params.id === 'string' ? params.id : Array.isArray(params.id) ? params.id[0] : '';
  const router = useRouter();
  
  const drawerGridRef = React.useRef<{ startBinPlacement: (bin: { id: string; width: number; depth: number; }) => void }>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [drawer, setDrawer] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [baseplates, setBaseplates] = useState<any[]>([]);
  
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
  
  // Fetch drawer data when component mounts
  useEffect(() => {
    const fetchDrawerData = async () => {
      if (!drawerId) {
        setError('Invalid drawer ID');
        setIsLoading(false);
        return;
      }
      
      try {
        setIsLoading(true);
        const drawerData = await getDrawer(parseInt(drawerId));
        
        setDrawer(drawerData);
        
        // Convert drawer bins to the format expected by DrawerGrid
        if (drawerData.bins && Array.isArray(drawerData.bins)) {
          const formattedBins = drawerData.bins.map((bin: any) => ({
            id: bin.id.toString(),
            width: bin.width,
            depth: bin.depth,
            x: bin.x_position,
            y: bin.y_position,
            unitX: Math.round(bin.x_position / 42),
            unitY: Math.round(bin.y_position / 42),
            unitWidth: Math.round(bin.width / 42),
            unitDepth: Math.round(bin.depth / 42)
          }));
          
          setPlacedBins(formattedBins);
          if (drawerData.baseplates && Array.isArray(drawerData.baseplates)) {
            setBaseplates(drawerData.baseplates);
          }
        }

        if (drawerData.baseplates && Array.isArray(drawerData.baseplates)) {
          console.log("Setting baseplates:", drawerData.baseplates);
          setBaseplates(drawerData.baseplates);
        } else {
          console.warn("Baseplates data is missing or not an array:", drawerData.baseplates);
        }
        
        // Set grid data or calculate it if not available
        if (drawerData.grid_units && Array.isArray(drawerData.grid_units) && drawerData.grid_units.length > 0) {
          setGridData({
            units: drawerData.grid_units,
            gridSizeX: drawerData.grid_size_x || Math.ceil(drawerData.width / 42),
            gridSizeY: drawerData.grid_size_y || Math.ceil(drawerData.depth / 42)
          });
        } else {
          // Calculate drawer grid if it's not available
          try {
            const calculatedGrid = await calculateDrawerGrid({
              name: drawerData.name,
              width: drawerData.width,
              depth: drawerData.depth,
              height: drawerData.height
            });
            
            setGridData(calculatedGrid);
          } catch (gridError) {
            console.error('Error calculating drawer grid:', gridError);
            // If calculation fails, create a simple grid based on dimensions
            const simpleGridSizeX = Math.ceil(drawerData.width / 42);
            const simpleGridSizeY = Math.ceil(drawerData.depth / 42);
            
            // Create uniform grid units
            const units = [];
            for (let y = 0; y < simpleGridSizeY; y++) {
              for (let x = 0; x < simpleGridSizeX; x++) {
                units.push({
                  width: 42,
                  depth: 42,
                  x_offset: x * 42,
                  y_offset: y * 42,
                  is_standard: true
                });
              }
            }
            
            setGridData({
              units,
              gridSizeX: simpleGridSizeX,
              gridSizeY: simpleGridSizeY
            });
          }
        }
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching drawer:', error);
        setError('Failed to load drawer. Please try again.');
        setIsLoading(false);
      }
    };

    fetchDrawerData();
  }, [drawerId]);

  useEffect(() => {
    const fetchBaseplates = async () => {
      if (!drawerId) return;

      try {
        console.log("Fetching baseplates for drawer:", drawerId);
        const baseplatesData = await getDrawerBaseplates(parseInt(drawerId));
        console.log("Received baseplates:", baseplatesData);
        setBaseplates(baseplatesData || []);
      } catch (error) {
        console.error("Error fetching baseplates:", error);
      }
    };

    // Only fetch baseplates after the drawer has loaded
    if (!isLoading && drawer) {
      fetchBaseplates();
    }
  }, [drawerId, isLoading, drawer]);

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

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto p-4 space-y-6">
        <NavigationHeader />
        <div className="animate-pulse">Loading drawer details...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto p-4 space-y-6">
        <NavigationHeader />
        <div className="p-4 bg-red-50 border border-red-200 rounded-md text-red-800">
          {error}
        </div>
        <Button onClick={() => router.push('/dashboard')}>
          Back to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      <NavigationHeader />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{drawer?.name || 'View Drawer'}</h1>
          <p className="text-gray-500">Edit bin placement and generate models</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push(`/edit-drawer/${drawerId}`)}>
            Edit Dimensions
          </Button>
          <Button variant="outline" onClick={() => router.push('/dashboard')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Drawer Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">Width</div>
              <div className="font-medium">{drawer?.width || 0}mm</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Depth</div>
              <div className="font-medium">{drawer?.depth || 0}mm</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Height</div>
              <div className="font-medium">{drawer?.height || 0}mm</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
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
                      if (!drawer || !drawerId) return;
                      
                      try {
                        setIsSaving(true);
                        setSaveSuccess(false);
                        setError(null);
                        
                        await updateDrawerBins(parseInt(drawerId), placedBins);
                        
                        setSaveSuccess(true);
                        // Automatically hide success message after 3 seconds
                        setTimeout(() => setSaveSuccess(false), 3000);
                      } catch (err) {
                        console.error("Error saving bins:", err);
                        setError("Failed to save bin placements");
                      } finally {
                        setIsSaving(false);
                      }
                    }}
                    disabled={isSaving}
                    className="px-3 py-1 text-sm bg-green-50 text-green-600 hover:bg-green-100 rounded disabled:opacity-50"
                  >
                    {isSaving ? "Saving..." : "Save Bin Placement"}
                  </button>
                  <button
                    onClick={async () => {
                      if (!drawer) return;
                      
                      try {
                        setIsGeneratingModels(true);
                        setError(null);
                        setGenerationSuccess(null);
                        
                        const result = await generateDrawerModels({
                          name: drawer.name,
                          width: drawer.width,
                          depth: drawer.depth,
                          height: drawer.height,
                          drawer_id: +drawerId,
                          bins: placedBins
                        });
                        
                        setGenerationSuccess({
                          message: `Drawer "${drawer.name}" models generated successfully!`,
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
                      <td className="px-4 py-2">{bin.id.split('-')[0] || bin.id}</td>
                      <td className="px-4 py-2">{bin.width}mm × {bin.depth}mm</td>
                      <td className="px-4 py-2">({bin.x}, {bin.y})</td>
                      <td className="px-4 py-2">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleRemoveBin(bin.id)}
                            className="text-red-500 hover:text-red-700"
                          >
                            Remove
                          </button>
                          {/* Only show these buttons for generated models (real bins with numeric IDs) */}
                          {!bin.id.includes('-') && (
                            <>
                              <button
                                onClick={() => {
                                  // We'll need to get the actual STL file path for this bin
                                  router.push(`/stl-view?url=/api/models/view/${bin.id}/stl`); 
                                }}
                                className="text-blue-500 hover:text-blue-700"
                              >
                                View STL
                              </button>
                              <button
                                onClick={() => window.open(`/api/models/view/${bin.id.split('-')[0]}/cad`, '_blank')}
                                className="text-green-500 hover:text-green-700"
                              >
                                Download CAD
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {saveSuccess && (
                <div className="mt-4 p-3 bg-green-50 text-green-700 rounded">
                  <div className="font-medium">Bin placement saved successfully!</div>
                  <div className="mt-1 text-sm">Your bin arrangements have been saved to the drawer.</div>
                </div>
              )}
              
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
          {/* Add this after the Placed Bins section */}
          <div style={{display: 'none'}}>
            DEBUG Baseplates: {JSON.stringify({
              count: baseplates.length,
              data: baseplates
            })}
          </div>
          {baseplates.length > 0 && (
            <div className="border rounded-lg p-4 bg-white mt-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">Baseplates</h2>
              </div>

              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">Size</th>
                    <th className="px-4 py-2 text-left">Files</th>
                  </tr>
                </thead>
                <tbody>
                  {baseplates.map((baseplate) => (
                    <tr key={baseplate.id} className="border-t">
                      <td className="px-4 py-2">{baseplate.id}</td>
                      <td className="px-4 py-2">{baseplate.width}mm × {baseplate.depth}mm</td>
                      <td className="px-4 py-2">
                        <div className="flex flex-col space-y-2">
                          {/* Show a section for each file if there are files */}
                          {baseplate.files && baseplate.files.length > 0 ? (
                            baseplate.files.map((file, index) => (
                              <div key={file.id || index} className="flex space-x-2 items-center">
                                <span className="text-gray-500">{file.file_type || `File ${index+1}`}:</span>
                                <button
                                  onClick={() => {
                                    router.push(`/stl-view?url=/api/baseplates/${baseplate.id}/files/${file.id}/stl`);
                                  }}
                                  className="text-blue-500 hover:text-blue-700"
                                >
                                  View
                                </button>
                                <button
                                  onClick={() => window.open(`/api/baseplates/${baseplate.id}/files/${file.id}/cad`, '_blank')}
                                  className="text-green-500 hover:text-green-700"
                                >
                                  Download
                                </button>
                              </div>
                            ))
                          ) : (
                            <div className="flex space-x-2">
                              {/* Fallback to using the baseplate ID directly if no files array */}
                              <button
                                onClick={() => {
                                  // Use baseplate-specific endpoint
                                  router.push(`/stl-view?url=/api/models/view/${baseplate.id}/baseplate/stl`);
                                }}
                                className="text-blue-500 hover:text-blue-700"
                              >
                                View STL
                              </button>
                              <button
                                onClick={() => window.open(`/api/models/view/${baseplate.id}/baseplate/cad`, '_blank')}
                                className="text-green-500 hover:text-green-700"
                              >
                                Download CAD
                              </button>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}