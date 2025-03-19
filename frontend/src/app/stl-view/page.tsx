'use client';

import React, { Suspense } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import STLViewer from '@/components/viewers/STLViewer';
import { useSearchParams } from 'next/navigation';
import { MousePointer, Move, RotateCcw, ZoomIn } from 'lucide-react';
import { ensureCorrectApiUrl } from '@/lib/api';

const ViewerInstructions = () => (
  <div className="mb-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <Card className="bg-secondary">
      <CardContent className="p-4 flex items-center space-x-4">
        <MousePointer className="h-6 w-6" />
        <div>
          <p className="font-medium">Rotate</p>
          <p className="text-sm text-muted-foreground">Left click + drag</p>
        </div>
      </CardContent>
    </Card>

    <Card className="bg-secondary">
      <CardContent className="p-4 flex items-center space-x-4">
        <Move className="h-6 w-6" />
        <div>
          <p className="font-medium">Pan</p>
          <p className="text-sm text-muted-foreground">Right click + drag</p>
        </div>
      </CardContent>
    </Card>

    <Card className="bg-secondary">
      <CardContent className="p-4 flex items-center space-x-4">
        <ZoomIn className="h-6 w-6" />
        <div>
          <p className="font-medium">Zoom</p>
          <p className="text-sm text-muted-foreground">Mouse wheel or pinch</p>
        </div>
      </CardContent>
    </Card>

    <Card className="bg-secondary">
      <CardContent className="p-4 flex items-center space-x-4">
        <RotateCcw className="h-6 w-6" />
        <div>
          <p className="font-medium">Reset View</p>
          <p className="text-sm text-muted-foreground">Double click</p>
        </div>
      </CardContent>
    </Card>
  </div>
);

// Create a wrapper component that uses searchParams
function STLViewContent() {
  const searchParams = useSearchParams();
  const modelUrl = searchParams.get('url');
  
  // Only log errors if there's no URL but we're not in the initial render
  // This helps prevent console spam
  if (!modelUrl && typeof window !== 'undefined' && document.referrer) {
    console.error('No model URL provided in query parameters');
    const params = Object.fromEntries(searchParams.entries());
    console.error('Available search params:', params);
  }
  
  // Try to get a valid URL even if it's empty or needs fixing
  const correctedUrl = modelUrl ? ensureCorrectApiUrl(modelUrl) : null;

  if (!modelUrl) {
    return (
      <div className="p-8">
        <Card>
          <CardHeader>
            <CardTitle>Error</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertDescription>No model URL provided</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Model Viewer</CardTitle>
        </CardHeader>
        <CardContent>
          <ViewerInstructions />
          <div className="border rounded-lg overflow-hidden">
            <div className="h-[600px]">
              <STLViewer url={correctedUrl || modelUrl} />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Main page component wrapped in Suspense
export default function StlViewPage() {
  // Get the searchParams in the main component
  const searchParams = useSearchParams();
  const hasModelParam = searchParams.has('url');

  // If there's no url parameter, show instructions instead of loading the model viewer
  if (!hasModelParam) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>STL Model Viewer</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertDescription>
                Please provide a model URL using the <code>url</code> query parameter. 
                For example: <code>/stl-view?url=/path/to/model.stl</code>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Normal loading state with Suspense
  return (
    <Suspense fallback={
      <div className="p-8 max-w-7xl mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Loading...</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="animate-pulse space-y-4">
              <div className="h-32 bg-secondary rounded"></div>
              <div className="h-[600px] bg-secondary rounded"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    }>
      <STLViewContent />
    </Suspense>
  );
}