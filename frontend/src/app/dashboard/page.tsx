'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getToken } from '@/lib/auth';

export default function Dashboard() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      window.location.href = '/login';
    } else {
      setIsLoading(false);
    }
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              Loading...
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <Card>
          <CardHeader>
            <CardTitle>Drawer Management</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={() => router.push('/drawer')}
              className="w-full"
            >
              Create New Drawer
            </Button>
            <Button
              onClick={() => router.push('/direct-generate')}
              className="w-full"
            >
              Direct Generate
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}