'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import STLViewer from '@/components/viewers/STLViewer';
import { useSearchParams } from 'next/navigation';

export default function StlViewPage() {
  const searchParams = useSearchParams();
  const modelUrl = searchParams.get('url');

  if (!modelUrl) {
    return (
      <div className="p-8">
        <Card>
          <CardHeader>
            <CardTitle>Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p>No model URL provided</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8">
      <Card>
        <CardHeader>
          <CardTitle>Model Viewer</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="w-full h-[600px]">
            <STLViewer url={modelUrl} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}