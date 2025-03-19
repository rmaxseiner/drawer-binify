'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import { getUserSettings, updateUserSettings, UserSettings } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from '@/components/ui/use-toast';

export default function SettingsPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [defaultDrawerHeight, setDefaultDrawerHeight] = useState('40');
  const [defaultBinHeight, setDefaultBinHeight] = useState('25');
  const [theme, setTheme] = useState('light');
  const { toast } = useToast();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const loadSettings = async () => {
      try {
        setIsLoading(true);
        const data = await getUserSettings();
        if (data) {
          setSettings(data);
          setDefaultDrawerHeight(data.default_drawer_height.toString());
          setDefaultBinHeight(data.default_bin_height.toString());
          setTheme(data.theme || 'light');
        }
      } catch (error) {
        console.error("Failed to load settings:", error);
        toast({
          title: "Error",
          description: "Failed to load your settings. Please try again.",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadSettings();
  }, [router]);

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      
      const updatedSettings = {
        default_drawer_height: parseFloat(defaultDrawerHeight),
        default_bin_height: parseFloat(defaultBinHeight),
        theme: theme
      };
      
      const result = await updateUserSettings(updatedSettings);
      
      toast({
        title: "Success",
        description: "Your settings have been saved successfully.",
      });
      
      // Update local state with the response
      setSettings(result);
      
      // After successful save, return to dashboard settings tab
      setTimeout(() => {
        // Using setTimeout to allow the toast to be seen briefly
        router.push('/dashboard');
        // We'll need a way to activate the settings tab in the dashboard
        // This is handled by localStorage and checked on dashboard load
        localStorage.setItem('activeMenu', 'settings');
      }, 1000);
    } catch (error) {
      console.error("Failed to save settings:", error);
      toast({
        title: "Error",
        description: "Failed to save your settings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-10">
        <Card className="max-w-md mx-auto">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-10">
      <div className="max-w-md mx-auto space-y-4">
        <Button 
          variant="outline" 
          onClick={() => {
            router.push('/dashboard');
            localStorage.setItem('activeMenu', 'settings');
          }}
          className="items-center flex"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
          Back to Settings
        </Button>
        
        <Card>
          <CardHeader>
            <CardTitle>Application Settings</CardTitle>
            <p className="text-sm text-gray-500">Customize your Drawerfinity experience</p>
          </CardHeader>
        <CardContent>
          <div className="space-y-4">
            
            <div className="space-y-2">
              <Label htmlFor="default-drawer-height">Default Drawer Height (mm)</Label>
              <Input
                id="default-drawer-height"
                type="number"
                value={defaultDrawerHeight}
                onChange={(e) => setDefaultDrawerHeight(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="default-bin-height">Default Bin Height (mm)</Label>
              <Input
                id="default-bin-height"
                type="number"
                value={defaultBinHeight}
                onChange={(e) => setDefaultBinHeight(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <select
                id="theme"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
            </div>
            
            <div className="flex flex-col gap-2 pt-4">
              <Button 
                onClick={handleSaveSettings}
                disabled={isSaving}
              >
                {isSaving ? "Saving..." : "Save Settings"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
  );
}