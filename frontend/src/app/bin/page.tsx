'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { getToken } from '@/lib/auth';

export default function BinPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push('/login');
    }
  }, [router]);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Bin Management</CardTitle>
        </CardHeader>
        <CardContent>
          {/* Add bin management content here */}
          <p>Bin management interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  );
}