'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getDrawer, updateDrawer } from '@/lib/api';
import Link from 'next/link';

export default function EditDrawerPage() {
  const params = useParams();
  const drawerId = typeof params.id === 'string' ? params.id : Array.isArray(params.id) ? params.id[0] : '';
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { register, handleSubmit, setValue, formState: { errors } } = useForm({
    defaultValues: {
      name: '',
      width: 0,
      depth: 0,
      height: 0
    }
  });

  useEffect(() => {
    const fetchDrawer = async () => {
      if (!drawerId) {
        setError('Invalid drawer ID');
        setIsLoading(false);
        return;
      }
      
      try {
        setIsLoading(true);
        const drawer = await getDrawer(parseInt(drawerId));
        
        // Set form values
        setValue('name', drawer.name);
        setValue('width', drawer.width);
        setValue('depth', drawer.depth);
        setValue('height', drawer.height);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching drawer:', error);
        setError('Failed to load drawer. Please try again.');
        setIsLoading(false);
      }
    };

    fetchDrawer();
  }, [drawerId, setValue]);

  const onSubmit = async (data: any) => {
    if (!drawerId) {
      setError('Invalid drawer ID');
      return;
    }
    
    try {
      setIsLoading(true);
      await updateDrawer(parseInt(drawerId), {
        name: data.name,
        width: parseFloat(data.width),
        depth: parseFloat(data.depth),
        height: parseFloat(data.height)
      });
      
      // Navigate back to dashboard
      router.push('/dashboard');
      router.refresh(); // Refresh to get updated data
    } catch (error) {
      console.error('Error updating drawer:', error);
      setError('Failed to update drawer. Please try again.');
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-4">
        <div className="max-w-lg mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              <div className="animate-pulse">Loading drawer details...</div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-4">
        <div className="max-w-lg mx-auto">
          <Card>
            <CardContent className="p-8 text-center">
              <div className="text-red-500">{error}</div>
              <Button className="mt-4" onClick={() => router.push('/dashboard')}>
                Back to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-lg mx-auto">
        <Card>
          <CardHeader>
            <CardTitle>Edit Drawer</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Drawer Name</Label>
                <Input
                  id="name"
                  {...register('name', { required: 'Drawer name is required' })}
                />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name.message}</p>
                )}
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="width">Width (mm)</Label>
                  <Input
                    id="width"
                    type="number"
                    {...register('width', { 
                      required: 'Width is required',
                      min: { value: 10, message: 'Width must be at least 10mm' },
                      valueAsNumber: true
                    })}
                  />
                  {errors.width && (
                    <p className="text-sm text-red-500">{errors.width.message}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="depth">Depth (mm)</Label>
                  <Input
                    id="depth"
                    type="number"
                    {...register('depth', { 
                      required: 'Depth is required',
                      min: { value: 10, message: 'Depth must be at least 10mm' },
                      valueAsNumber: true
                    })}
                  />
                  {errors.depth && (
                    <p className="text-sm text-red-500">{errors.depth.message}</p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="height">Height (mm)</Label>
                  <Input
                    id="height"
                    type="number"
                    {...register('height', { 
                      required: 'Height is required',
                      min: { value: 5, message: 'Height must be at least 5mm' },
                      valueAsNumber: true
                    })}
                  />
                  {errors.height && (
                    <p className="text-sm text-red-500">{errors.height.message}</p>
                  )}
                </div>
              </div>
              
              <div className="flex justify-between pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.push('/dashboard')}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </Button>
                <Button 
                  type="button"
                  variant="secondary"
                  disabled={isLoading}
                  onClick={async () => {
                    const formData = {
                      name: (document.getElementById('name') as HTMLInputElement)?.value || '',
                      width: parseFloat((document.getElementById('width') as HTMLInputElement)?.value || '0'),
                      depth: parseFloat((document.getElementById('depth') as HTMLInputElement)?.value || '0'),
                      height: parseFloat((document.getElementById('height') as HTMLInputElement)?.value || '0'),
                    };
                    
                    if (formData.name && formData.width > 0 && formData.depth > 0 && formData.height > 0) {
                      try {
                        setIsLoading(true);
                        await updateDrawer(parseInt(drawerId), formData);
                        router.push(`/view-drawer/${drawerId}`);
                      } catch (error) {
                        console.error('Error updating drawer:', error);
                        setError('Failed to update drawer. Please try again.');
                        setIsLoading(false);
                      }
                    }
                  }}
                >
                  Save & Edit Bins
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}