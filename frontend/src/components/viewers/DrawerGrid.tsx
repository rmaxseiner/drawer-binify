import React, { useRef, useEffect, useState } from 'react';

interface Unit {
  width: number;
  depth: number;
  x_offset: number;
  y_offset: number;
  is_standard: boolean;
}

interface PlacedBin {
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

interface DrawerGridProps {
  units: Unit[];
  gridSizeX: number;
  gridSizeY: number;
  placedBins: PlacedBin[];
  onPlaceBin: (bin: PlacedBin) => void;
  onRemoveBin: (binId: string) => void;
}

export const DrawerGrid = React.forwardRef<
  { startBinPlacement: (bin: { id: string; width: number; depth: number; }) => void },
  DrawerGridProps
>(({ units, gridSizeX, gridSizeY, placedBins = [], onPlaceBin, onRemoveBin }, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scale, setScale] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Calculate the total width and height of the drawer
  const drawerWidth = units.reduce((max, unit) => Math.max(max, unit.x_offset + unit.width), 0);
  const drawerDepth = units.reduce((max, unit) => Math.max(max, unit.y_offset + unit.depth), 0);

  // Track if we're currently placing a bin
  const [placingBin, setPlacingBin] = useState<{
    width: number;
    depth: number;
    id: string;
    x: number;
    y: number;
  } | null>(null);
  
  // Track which unit is currently being hovered over
  const [hoveredUnit, setHoveredUnit] = useState<{
    x: number;
    y: number;
    width: number;
    depth: number;
  } | null>(null);
  
  // Track which bin is currently selected
  const [selectedBin, setSelectedBin] = useState<string | null>(null);

  // Setup canvas and draw initial grid
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const updateCanvasSize = () => {
      const containerRect = container.getBoundingClientRect();
      canvas.width = containerRect.width;
      canvas.height = 500; // Fixed height, could be made responsive
    };

    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);
    
    renderGrid();

    return () => {
      window.removeEventListener('resize', updateCanvasSize);
    };
  }, [units, scale, position, drawerWidth, drawerDepth, gridSizeX, gridSizeY, placedBins, placingBin, hoveredUnit, selectedBin]);

  // Helper function to find a unit at a given canvas coordinate
  const findUnitAtPosition = (x: number, y: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    
    // Calculate a padding around the drawer
    const padding = 20;
    
    // Calculate the scale to fit the entire drawer within the canvas
    const scaleX = (canvas.width - padding * 2) / drawerWidth;
    const scaleY = (canvas.height - padding * 2) / drawerDepth;
    const autoScale = Math.min(scaleX, scaleY);
    
    // Apply the current scale and position
    const actualScale = scale * autoScale;
    
    // Center the drawer
    const translateX = (canvas.width - drawerWidth * actualScale) / 2 + position.x;
    const translateY = (canvas.height - drawerDepth * actualScale) / 2 + position.y;
    
    // Convert canvas coordinates to drawer coordinates
    const drawerX = (x - translateX) / actualScale;
    const drawerY = (y - translateY) / actualScale;
    
    // Find the unit that contains this point
    for (const unit of units) {
      if (
        drawerX >= unit.x_offset && 
        drawerX < unit.x_offset + unit.width &&
        drawerY >= unit.y_offset && 
        drawerY < unit.y_offset + unit.depth
      ) {
        return unit;
      }
    }
    
    return null;
  };
  
  // Helper function to get the adjusted bin dimensions based on the grid
  const getAdjustedBinDimensions = (
    origX: number, 
    origY: number, 
    origWidth: number, 
    origDepth: number
  ) => {
    // Estimate how many grid units this bin intends to cover
    const intendedGridWidth = Math.round(origWidth / 42);
    const intendedGridDepth = Math.round(origDepth / 42);
    
    // Track which units the bin covers
    const coveredUnits: typeof units = [];
    
    // Find all units that would be covered by this bin
    for (const unit of units) {
      // Check if this unit is overlapped by the bin
      const unitRight = unit.x_offset + unit.width;
      const unitBottom = unit.y_offset + unit.depth;
      const binRight = origX + origWidth;
      const binBottom = origY + origDepth;
      
      // Check for horizontal and vertical overlap
      const horizontalOverlap = (origX < unitRight) && (binRight > unit.x_offset);
      const verticalOverlap = (origY < unitBottom) && (binBottom > unit.y_offset);
      
      if (horizontalOverlap && verticalOverlap) {
        coveredUnits.push(unit);
      }
    }
    
    if (coveredUnits.length === 0) {
      return { width: origWidth, depth: origDepth };
    }
    
    // Sort units by their x and y positions for easier processing
    const sortedByX = [...coveredUnits].sort((a, b) => a.x_offset - b.x_offset);
    const sortedByY = [...coveredUnits].sort((a, b) => a.y_offset - b.y_offset);
    
    // Find the start unit (top-left corner)
    const startUnit = coveredUnits.find(unit => 
      unit.x_offset === origX && unit.y_offset === origY
    ) || coveredUnits[0];
    
    // Find all units in the same row and column as the start unit
    let widthUnits = [];
    let depthUnits = [];
    
    // Find units in the same row (for width calculation)
    let currentX = startUnit.x_offset;
    for (let i = 0; i < intendedGridWidth; i++) {
      const unitsAtCurrentX = coveredUnits.filter(unit => 
        Math.abs(unit.x_offset - currentX) < 1 && 
        unit.y_offset === startUnit.y_offset
      );
      
      if (unitsAtCurrentX.length === 0) break;
      
      widthUnits.push(unitsAtCurrentX[0]);
      currentX += unitsAtCurrentX[0].width;
    }
    
    // Find units in the same column (for depth calculation)
    let currentY = startUnit.y_offset;
    for (let i = 0; i < intendedGridDepth; i++) {
      const unitsAtCurrentY = coveredUnits.filter(unit => 
        Math.abs(unit.y_offset - currentY) < 1 && 
        unit.x_offset === startUnit.x_offset
      );
      
      if (unitsAtCurrentY.length === 0) break;
      
      depthUnits.push(unitsAtCurrentY[0]);
      currentY += unitsAtCurrentY[0].depth;
    }
    
    // Calculate total width and depth based on the units found
    let adjustedWidth = widthUnits.reduce((sum, unit) => sum + unit.width, 0);
    let adjustedDepth = depthUnits.reduce((sum, unit) => sum + unit.depth, 0);
    
    // If we didn't find any units in a row/column, fallback to the original dimensions
    if (widthUnits.length === 0) adjustedWidth = origWidth;
    if (depthUnits.length === 0) adjustedDepth = origDepth;
    
    // Make sure we don't exceed the intended grid coverage
    if (adjustedWidth > origWidth) adjustedWidth = origWidth;
    if (adjustedDepth > origDepth) adjustedDepth = origDepth;
    
    return { width: adjustedWidth, depth: adjustedDepth };
  };
  
  // Helper function to find a placed bin at a given position
  const findBinAtPosition = (x: number, y: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    
    // Calculate a padding around the drawer
    const padding = 20;
    
    // Calculate the scale to fit the entire drawer within the canvas
    const scaleX = (canvas.width - padding * 2) / drawerWidth;
    const scaleY = (canvas.height - padding * 2) / drawerDepth;
    const autoScale = Math.min(scaleX, scaleY);
    
    // Apply the current scale and position
    const actualScale = scale * autoScale;
    
    // Center the drawer
    const translateX = (canvas.width - drawerWidth * actualScale) / 2 + position.x;
    const translateY = (canvas.height - drawerDepth * actualScale) / 2 + position.y;
    
    // Convert canvas coordinates to drawer coordinates
    const drawerX = (x - translateX) / actualScale;
    const drawerY = (y - translateY) / actualScale;
    
    // Find the bin that contains this point
    for (const bin of placedBins) {
      if (
        drawerX >= bin.x && 
        drawerX < bin.x + bin.width &&
        drawerY >= bin.y && 
        drawerY < bin.y + bin.depth
      ) {
        return bin;
      }
    }
    
    return null;
  };

  // Check if a unit grid is available (not covered by a bin)
  const isUnitAvailable = (unitX: number, unitY: number) => {
    // Find the unit
    const unit = units.find(u => 
      u.x_offset === unitX && 
      u.y_offset === unitY
    );
    
    if (!unit) return false;
    
    // Check if any bin covers this unit
    for (const bin of placedBins) {
      if (
        unitX >= bin.x && 
        unitX < bin.x + bin.width &&
        unitY >= bin.y && 
        unitY < bin.y + bin.depth
      ) {
        return false;
      }
      
      if (
        bin.x >= unitX && 
        bin.x < unitX + unit.width &&
        bin.y >= unitY && 
        bin.y < unitY + unit.depth
      ) {
        return false;
      }
      
      // Check if bin overlaps unit
      if (
        (bin.x <= unitX && bin.x + bin.width > unitX) || 
        (unitX <= bin.x && unitX + unit.width > bin.x)
      ) {
        if (
          (bin.y <= unitY && bin.y + bin.depth > unitY) || 
          (unitY <= bin.y && unitY + unit.depth > bin.y)
        ) {
          return false;
        }
      }
    }
    
    return true;
  };
  
  // Check if a new bin would overlap with existing bins or be outside the grid
  const wouldBinOverlap = (x: number, y: number, width: number, depth: number) => {
    // Check if the bin would be inside the grid boundaries
    const binRight = x + width;
    const binBottom = y + depth;
    const drawerRight = units.reduce((max, unit) => Math.max(max, unit.x_offset + unit.width), 0);
    const drawerBottom = units.reduce((max, unit) => Math.max(max, unit.y_offset + unit.depth), 0);
    
    if (x < 0 || y < 0 || binRight > drawerRight || binBottom > drawerBottom) {
      return true; // Outside grid boundaries
    }
    
    // Check if the new bin would overlap with any existing bin
    for (const bin of placedBins) {
      // Check if bins overlap horizontally
      const xOverlap = (x < bin.x + bin.width) && (x + width > bin.x);
      // Check if bins overlap vertically
      const yOverlap = (y < bin.y + bin.depth) && (y + depth > bin.y);
      
      // If both overlap, then the bins intersect
      if (xOverlap && yOverlap) {
        return true;
      }
    }
    
    return false;
  };

  // Render the grid
  const renderGrid = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Set background
    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Calculate a padding around the drawer
    const padding = 20;
    
    // Calculate the scale to fit the entire drawer within the canvas
    const scaleX = (canvas.width - padding * 2) / drawerWidth;
    const scaleY = (canvas.height - padding * 2) / drawerDepth;
    const autoScale = Math.min(scaleX, scaleY);
    
    // Apply the current scale and position
    const actualScale = scale * autoScale;
    
    // Center the drawer
    const translateX = (canvas.width - drawerWidth * actualScale) / 2 + position.x;
    const translateY = (canvas.height - drawerDepth * actualScale) / 2 + position.y;
    
    // First, draw each grid unit
    for (const unit of units) {
      const x = unit.x_offset * actualScale + translateX;
      const y = unit.y_offset * actualScale + translateY;
      const width = unit.width * actualScale;
      const depth = unit.depth * actualScale;
      
      // Check if this unit is covered by a bin
      const isUnitCovered = placedBins.some(bin => {
        const binLeft = bin.x;
        const binRight = bin.x + bin.width;
        const binTop = bin.y;
        const binBottom = bin.y + bin.depth;
        
        const unitLeft = unit.x_offset;
        const unitRight = unit.x_offset + unit.width;
        const unitTop = unit.y_offset;
        const unitBottom = unit.y_offset + unit.depth;
        
        // Check if the bin fully contains this unit
        return (
          binLeft <= unitLeft && 
          binRight >= unitRight &&
          binTop <= unitTop && 
          binBottom >= unitBottom
        );
      });
      
      // Draw unit rectangle with appropriate color
      ctx.strokeStyle = '#888';
      ctx.lineWidth = 1;
      
      if (isUnitCovered) {
        // If covered by a bin, make it grey but still show the grid
        ctx.fillStyle = '#e0e0e0';
      } else {
        // Otherwise use the standard color scheme
        ctx.fillStyle = unit.is_standard ? '#c8e6c9' : '#ffcdd2'; // Green for standard, red for non-standard
      }
      
      ctx.fillRect(x, y, width, depth);
      ctx.strokeRect(x, y, width, depth);
      
      // Add text showing the unit dimensions if big enough and not covered
      if (width > 40 && depth > 40 && !isUnitCovered) {
        ctx.fillStyle = '#000';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const text = `${Math.round(unit.width)}x${Math.round(unit.depth)}`;
        ctx.fillText(text, x + width / 2, y + depth / 2);
      }
    }
    
    // Then, draw the placed bins
    for (const bin of placedBins) {
      const x = bin.x * actualScale + translateX;
      const y = bin.y * actualScale + translateY;
      const width = bin.width * actualScale;
      const depth = bin.depth * actualScale;
      
      // Fill with a semi-transparent color so grid lines can still be seen beneath
      ctx.fillStyle = bin.id === selectedBin ? 'rgba(100, 149, 237, 0.7)' : 'rgba(150, 150, 150, 0.7)';
      ctx.fillRect(x, y, width, depth);
      
      // Draw a more prominent border
      ctx.strokeStyle = bin.id === selectedBin ? '#3060c0' : '#555';
      ctx.lineWidth = bin.id === selectedBin ? 3 : 2;
      ctx.strokeRect(x, y, width, depth);
      
      // Draw bin dimensions text
      if (width > 60 && depth > 60) {
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${Math.round(bin.width)}x${Math.round(bin.depth)}`, x + width / 2, y + depth / 2);
      }
    }
    
    // Draw hover preview if we're placing a bin and hovering over a valid unit
    if (placingBin && hoveredUnit) {
      const x = hoveredUnit.x * actualScale + translateX;
      const y = hoveredUnit.y * actualScale + translateY;
      
      // Get adjusted dimensions that respect non-standard grid units
      const { width: adjustedWidth, depth: adjustedDepth } = getAdjustedBinDimensions(
        hoveredUnit.x,
        hoveredUnit.y,
        placingBin.width,
        placingBin.depth
      );
      
      // Calculate the preview dimensions based on the adjusted bin dimensions
      const previewWidth = adjustedWidth * actualScale;
      const previewDepth = adjustedDepth * actualScale;
      
      // Check if the placement is valid:
      // 1. The unit exists in our grid
      // 2. The unit is available (not already covered by another bin)
      // 3. The bin being placed wouldn't overlap with any existing bins
      const unitExists = units.some(unit => 
        unit.x_offset === hoveredUnit.x && 
        unit.y_offset === hoveredUnit.y
      );
      
      const unitAvailable = isUnitAvailable(hoveredUnit.x, hoveredUnit.y);
      const noOverlap = !wouldBinOverlap(
        hoveredUnit.x, 
        hoveredUnit.y, 
        adjustedWidth, 
        adjustedDepth
      );
      
      const canPlace = unitExists && unitAvailable && noOverlap;
      
      // Draw preview with appropriate color
      ctx.fillStyle = canPlace ? 'rgba(76, 175, 80, 0.5)' : 'rgba(244, 67, 54, 0.5)';
      ctx.strokeStyle = canPlace ? '#388e3c' : '#d32f2f';
      ctx.lineWidth = 2;
      
      // Draw a dashed outline of the original bin size, if it's different from the adjusted size
      if (Math.abs(adjustedWidth - placingBin.width) > 0.1 || Math.abs(adjustedDepth - placingBin.depth) > 0.1) {
        ctx.setLineDash([5, 3]);
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.strokeRect(x, y, placingBin.width * actualScale, placingBin.depth * actualScale);
        ctx.setLineDash([]);
      }
      
      // Draw the adjusted bin preview
      ctx.fillRect(x, y, previewWidth, previewDepth);
      ctx.strokeRect(x, y, previewWidth, previewDepth);
      
      // Add text to show the adjusted dimensions
      if (previewWidth > 60 && previewDepth > 40) {
        ctx.fillStyle = '#000';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const text = `${Math.round(adjustedWidth)}x${Math.round(adjustedDepth)}mm`;
        ctx.fillText(text, x + previewWidth / 2, y + previewDepth / 2);
      }
    }
    
    // Draw a scale indicator
    ctx.fillStyle = '#000';
    ctx.font = '12px Arial';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText(`${gridSizeX}x${gridSizeY} grid (${drawerWidth}mm x ${drawerDepth}mm)`, 10, canvas.height - 10);
  };

  // Handle zoom with mouse wheel
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1; // Zoom in/out
    setScale(prevScale => Math.max(0.1, Math.min(5, prevScale * zoomFactor)));
  };

  // Handle bin placement and pan with mouse interactions
  const handleMouseDown = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (placingBin) {
      // We're currently placing a bin, check if we can place it at the hovered unit
      if (hoveredUnit) {
        // Check if the placement is valid:
        // 1. The unit exists in our grid
        // 2. The unit is available (not already covered by another bin)
        // 3. The bin being placed wouldn't overlap with any existing bins
        // Get adjusted dimensions for non-standard grid units
        const { width: adjustedWidth, depth: adjustedDepth } = getAdjustedBinDimensions(
          hoveredUnit.x,
          hoveredUnit.y,
          placingBin.width,
          placingBin.depth
        );
        
        const unitExists = units.some(unit => 
          unit.x_offset === hoveredUnit.x && 
          unit.y_offset === hoveredUnit.y
        );
        
        const unitAvailable = isUnitAvailable(hoveredUnit.x, hoveredUnit.y);
        const noOverlap = !wouldBinOverlap(
          hoveredUnit.x, 
          hoveredUnit.y, 
          adjustedWidth, 
          adjustedDepth
        );
        
        const canPlace = unitExists && unitAvailable && noOverlap;
        
        if (canPlace) {
          // Place the bin with adjusted dimensions
          onPlaceBin({
            id: placingBin.id,
            width: adjustedWidth,  // Use adjusted width
            depth: adjustedDepth,  // Use adjusted depth
            x: hoveredUnit.x,
            y: hoveredUnit.y,
            unitX: Math.round(hoveredUnit.x / 42), // Convert to grid units
            unitY: Math.round(hoveredUnit.y / 42), // Convert to grid units
            unitWidth: Math.round(adjustedWidth / 42), // Convert to grid units using adjusted width
            unitDepth: Math.round(adjustedDepth / 42), // Convert to grid units using adjusted depth
          });
          
          // Clear the placing state
          setPlacingBin(null);
          setHoveredUnit(null);
          return;
        }
      }
    } else {
      // Check if we clicked on an existing bin
      const clickedBin = findBinAtPosition(x, y);
      if (clickedBin) {
        // Select the bin
        setSelectedBin(selectedBin === clickedBin.id ? null : clickedBin.id);
        return;
      } else {
        // Deselect if we clicked outside a bin
        setSelectedBin(null);
      }
    }
    
    // If we're not placing a bin or didn't click on a bin, start panning
    setDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (placingBin) {
      // If we're in bin placement mode, update the hover unit
      const unit = findUnitAtPosition(x, y);
      if (unit) {
        setHoveredUnit({
          x: unit.x_offset,
          y: unit.y_offset,
          width: unit.width,
          depth: unit.depth
        });
      } else {
        setHoveredUnit(null);
      }
    } else if (dragging) {
      // If we're dragging, update the position
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setDragging(false);
  };
  
  // Handle keyboard events
  const handleKeyDown = (e: KeyboardEvent) => {
    // Delete key removes selected bin
    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (selectedBin) {
        onRemoveBin(selectedBin);
        setSelectedBin(null);
      }
    }
    
    // Escape key cancels bin placement
    if (e.key === 'Escape') {
      setPlacingBin(null);
      setHoveredUnit(null);
    }
  };
  
  // Set up keyboard event listeners
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [selectedBin]);

  // Add zoom buttons
  const handleZoomIn = () => {
    setScale(prevScale => Math.min(5, prevScale * 1.2));
  };

  const handleZoomOut = () => {
    setScale(prevScale => Math.max(0.1, prevScale * 0.8));
  };

  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  // Public method to start bin placement
  const startBinPlacement = (bin: { id: string, width: number, depth: number }) => {
    setSelectedBin(null);
    setPlacingBin({
      id: bin.id,
      width: bin.width,
      depth: bin.depth,
      x: 0,
      y: 0
    });
  };
  
  // Expose startBinPlacement method
  React.useImperativeHandle(ref, () => ({
    startBinPlacement
  }));

  // Close the DrawerGrid component
  return (
    <div className="flex flex-col">
      <div className="flex justify-between items-center space-x-2 mb-2">
        <div>
          {selectedBin && (
            <button
              onClick={() => {
                if (selectedBin) {
                  onRemoveBin(selectedBin);
                  setSelectedBin(null);
                }
              }}
              className="px-3 py-1 bg-red-50 text-red-600 hover:bg-red-100 rounded flex items-center gap-1 text-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 6h18"></path>
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
              </svg>
              Remove Selected Bin
            </button>
          )}
          {placingBin && (
            <button
              onClick={() => {
                setPlacingBin(null);
                setHoveredUnit(null);
              }}
              className="px-3 py-1 bg-orange-50 text-orange-600 hover:bg-orange-100 rounded flex items-center gap-1 text-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 6 6 18"></path>
                <path d="m6 6 12 12"></path>
              </svg>
              Cancel Placement
            </button>
          )}
        </div>
        <div className="flex space-x-2">
          <button 
            onClick={handleZoomIn}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded"
            aria-label="Zoom in"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="11" y1="8" x2="11" y2="14"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </button>
          <button 
            onClick={handleZoomOut}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded"
            aria-label="Zoom out"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </button>
          <button 
            onClick={handleReset}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded"
            aria-label="Reset view"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
              <path d="M3 3v5h5"></path>
            </svg>
          </button>
        </div>
      </div>
      
      <div 
        ref={containerRef} 
        className="border rounded-lg overflow-hidden bg-white"
        style={{ 
          cursor: placingBin 
            ? 'crosshair'
            : dragging 
              ? 'grabbing' 
              : selectedBin 
                ? 'pointer' 
                : 'grab' 
        }}
      >
        <canvas
          ref={canvasRef}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        <span>Scroll to zoom, drag to pan</span>
        <div className="mt-1 flex flex-wrap gap-3">
          <div>
            <span className="inline-block w-3 h-3 bg-green-100 border border-gray-300 mr-1"></span>
            <span className="mr-2">Standard unit</span>
          </div>
          <div>
            <span className="inline-block w-3 h-3 bg-red-100 border border-gray-300 mr-1"></span>
            <span className="mr-2">Non-standard unit</span>
          </div>
          <div>
            <span className="inline-block w-3 h-3 bg-gray-300 border border-gray-300 mr-1"></span>
            <span className="mr-2">Filled unit</span>
          </div>
          <div>
            <span className="inline-block w-3 h-3 bg-blue-200 border border-blue-400 mr-1"></span>
            <span>Selected bin</span>
          </div>
        </div>
        {selectedBin && (
          <div className="mt-1 text-blue-600">
            <span>Press Delete key to remove selected bin</span>
          </div>
        )}
      </div>
    </div>
  );
});
