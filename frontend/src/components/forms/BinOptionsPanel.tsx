import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface BinOption {
  id: string;
  width: number;
  depth: number;
  name: string;
  isAvailable: boolean;
}

interface BinOptionsPanelProps {
  gridSizeX: number;
  gridSizeY: number;
  maxPrintWidth: number;
  maxPrintDepth: number;
  onSelectBin?: (bin: { id: string; width: number; depth: number; }) => void;
}

// Standard grid size (42mm)
const GRID_SIZE = 42;

export function BinOptionsPanel({ gridSizeX, gridSizeY, maxPrintWidth, maxPrintDepth, onSelectBin }: BinOptionsPanelProps) {
  const [binOptions, setBinOptions] = useState<BinOption[][]>([]);
  
  // Generate bin options when the grid size changes
  useEffect(() => {
    if (gridSizeX <= 0 || gridSizeY <= 0) return;
    
    const options: BinOption[][] = [];
    
    // For each column (width)
    for (let width = 1; width <= gridSizeX; width++) {
      const columnOptions: BinOption[] = [];
      
      // For each row (depth)
      for (let depth = 1; depth <= gridSizeY; depth++) {
        // Calculate actual dimensions in mm
        const widthMM = width * GRID_SIZE;
        const depthMM = depth * GRID_SIZE;
        
        // Check if the bin would fit on the print bed
        const isAvailable = widthMM <= maxPrintWidth && depthMM <= maxPrintDepth;
        
        columnOptions.push({
          id: `bin-${width}x${depth}`,
          width: widthMM,
          depth: depthMM,
          name: `${width}x${depth}`,
          isAvailable
        });
      }
      
      options.push(columnOptions);
    }
    
    setBinOptions(options);
  }, [gridSizeX, gridSizeY, maxPrintWidth, maxPrintDepth]);
  
  if (binOptions.length === 0) {
    return null;
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Available Bin Options</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-6 gap-6">
          {binOptions.map((column, columnIndex) => (
            <div key={`column-${columnIndex}`} className="space-y-2">
              <h3 className="font-semibold">{columnIndex + 1}x Bins</h3>
              <div className="space-y-2">
                {column.map((bin) => (
                  <button
                    key={bin.id}
                    className={`w-full p-2 text-left border rounded ${
                      bin.isAvailable 
                        ? 'bg-white hover:bg-gray-50 cursor-pointer' 
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    }`}
                    disabled={!bin.isAvailable}
                    title={
                      bin.isAvailable 
                        ? `${bin.width}mm x ${bin.depth}mm - Click to place in drawer` 
                        : `Too large for print bed (${maxPrintWidth}mm x ${maxPrintDepth}mm)`
                    }
                    onClick={() => {
                      if (bin.isAvailable && onSelectBin) {
                        onSelectBin({
                          id: bin.id,
                          width: bin.width,
                          depth: bin.depth
                        });
                      }
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <span>{bin.name}</span>
                      {!bin.isAvailable && (
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
                        </svg>
                      )}
                      {bin.isAvailable && (
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                          <polyline points="9 14 12 17 21 8"></polyline>
                        </svg>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {bin.width}mm x {bin.depth}mm
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}