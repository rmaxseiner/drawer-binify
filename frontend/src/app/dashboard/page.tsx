'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getToken, removeToken, isAuthenticated } from '@/lib/auth';
import { getUserInfo, getUserDrawers } from '@/lib/api';
import Link from 'next/link';

export default function Dashboard() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<{ username: string; email: string; first_name: string; last_name: string } | null>(null);
  const [drawers, setDrawers] = useState<any[]>([]);
  const [activeMenu, setActiveMenu] = useState('drawers');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  
  // Add click outside listener
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const dropdown = document.getElementById('user-dropdown');
      const button = document.getElementById('user-dropdown-button');
      
      if (dropdown && button && 
          !dropdown.contains(event.target as Node) && 
          !button.contains(event.target as Node)) {
        dropdown.classList.add('hidden');
        setDropdownOpen(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    // Check if there's a stored activeMenu setting
    if (typeof window !== 'undefined') {
      const storedMenu = localStorage.getItem('activeMenu');
      if (storedMenu) {
        setActiveMenu(storedMenu);
        // Clear the stored setting after using it
        localStorage.removeItem('activeMenu');
      }
    }
    
    // Check authentication first
    if (!isAuthenticated()) {
      console.log("Not authenticated, redirecting to login");
      router.push('/login');
      return;
    }

    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        // Get user data
        try {
          console.log("Fetching user info");
          const userData = await getUserInfo();
          console.log("User data received:", userData);
          
          if (userData) {
            setUser(userData);
          } else {
            console.error("User data is empty");
            setUser(null);
          }
        } catch (userError) {
          console.error("Error fetching user data:", userError);
          if (userError instanceof Error && userError.message.includes('401')) {
            // If authentication error, redirect to login
            console.error("Authentication expired, redirecting to login");
            router.push('/login');
            return;
          }
          setUser(null);
        }
        
        // Get drawer data separately
        try {
          console.log("Fetching drawer data");
          const drawerData = await getUserDrawers();
          console.log("Drawer data received:", drawerData);
          
          if (Array.isArray(drawerData)) {
            setDrawers(drawerData);
          } else {
            console.error("Drawer data is not an array:", drawerData);
            setDrawers([]);
          }
        } catch (drawerError) {
          console.error("Error fetching drawer data:", drawerError);
          setDrawers([]);
        }
        
      } catch (error) {
        console.error("Error in fetch operation:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const handleLogout = () => {
    removeToken();
    window.location.href = '/login';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-96">
            <div className="animate-pulse">Loading...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation Bar */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Drawerfinity</h1>
            
            {user && (
              <div className="flex items-center gap-4">
                <div className="text-sm text-gray-700">
                  Logged in as <span className="font-medium">{user?.username || 'User'}</span>
                </div>
                <div className="relative">
                  <button 
                    id="user-dropdown-button"
                    onClick={() => {
                      const dropdown = document.getElementById('user-dropdown');
                      if (dropdown) {
                        dropdown.classList.toggle('hidden');
                        setDropdownOpen(!dropdownOpen);
                      }
                    }}
                    className="flex items-center gap-2 p-2 rounded-full hover:bg-gray-100"
                  >
                    <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white font-medium">
                      {user?.first_name?.[0] || user?.username?.[0] || 'U'}</div>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                      <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                    </svg>
                  </button>
                  <div id="user-dropdown" className="absolute right-0 top-full mt-1 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 hidden z-10">
                    <div className="block px-4 py-2 text-sm text-gray-700 border-b">
                      <div className="font-medium">{user?.first_name || ''} {user?.last_name || ''}</div>
                      <div className="text-gray-500">{user?.email || ''}</div>
                    </div>
                    <button 
                      onClick={() => router.push('/profile')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Profile
                    </button>
                    <button 
                      onClick={() => setActiveMenu('settings')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      App Settings
                    </button>
                    <button 
                      onClick={() => router.push('/profile/password')}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Change Password
                    </button>
                    <button 
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 border-t"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          {/* Sidebar Navigation */}
          <div className="w-full md:w-64 mb-8 md:mb-0">
            <Card>
              <CardContent className="p-4">
                <nav className="space-y-1">
                  <Button
                    variant={activeMenu === 'drawers' ? 'default' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => setActiveMenu('drawers')}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
                    </svg>
                    Manage Drawers
                  </Button>
                  
                  <Button
                    variant={activeMenu === 'generate' ? 'default' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => {
                      router.push('/direct-generate');
                    }}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                    Direct Generate
                  </Button>
                  
                  <Button
                    variant={activeMenu === 'models' ? 'default' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => router.push('/stl-view')}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
                      <path fillRule="evenodd" d="M13.707 3.293a1 1 0 010 1.414L9.414 9H13a1 1 0 110 2H7a1 1 0 01-1-1V4a1 1 0 112 0v3.586l4.293-4.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    View Models
                  </Button>
                  
                  <Button
                    variant={activeMenu === 'settings' ? 'default' : 'ghost'}
                    className="w-full justify-start"
                    onClick={() => setActiveMenu('settings')}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                    </svg>
                    Settings
                  </Button>
                </nav>
              </CardContent>
            </Card>
          </div>
          
          {/* Main Content Area */}
          <div className="flex-1">
            {activeMenu === 'drawers' && (
              <>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold">My Drawers</h2>
                  <Button
                    onClick={() => router.push('/create-drawer')}
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                    Create New Drawer
                  </Button>
                </div>
                
                {!Array.isArray(drawers) || drawers.length === 0 ? (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <div className="text-gray-500 mb-4">You haven't created any drawers yet.</div>
                      <Button
                        onClick={() => router.push('/create-drawer')}
                      >
                        Create Your First Drawer
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {drawers.map((drawer) => {
                      if (!drawer || !drawer.id) return null;
                      
                      return (
                        <Card key={drawer.id} className="overflow-hidden">
                          <div className="p-1 bg-gradient-to-r from-blue-100 to-indigo-100">
                            <div className="bg-gray-100 h-40 flex items-center justify-center">
                              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-20 h-20 text-gray-400">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 6.878V6a2.25 2.25 0 012.25-2.25h7.5A2.25 2.25 0 0118 6v.878m-12 0c.235-.083.487-.128.75-.128h10.5c.263 0 .515.045.75.128m-12 0A2.25 2.25 0 004.5 9v.878m13.5-3A2.25 2.25 0 0119.5 9v.878m0 0a2.246 2.246 0 00-.75-.128H5.25c-.263 0-.515.045-.75.128m15 0A2.25 2.25 0 0121 12v6a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 18v-6c0-.98.626-1.813 1.5-2.122" />
                              </svg>
                            </div>
                          </div>
                          <CardContent className="p-4">
                            <h3 className="text-lg font-medium mb-1">{drawer.name || 'Unnamed Drawer'}</h3>
                            <div className="text-sm text-gray-500 mb-2">
                              {drawer.width || 0}mm × {drawer.depth || 0}mm × {drawer.height || 0}mm
                            </div>
                            <div className="text-sm mb-2">
                              <span className="font-medium">{drawer.bins?.length || 0}</span> bins
                            </div>
                            <div className="flex gap-2 mt-3">
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="flex-1"
                                onClick={() => router.push(`/edit-drawer/${drawer.id}`)}
                              >
                                Edit
                              </Button>
                              <Button 
                                variant="outline" 
                                size="sm" 
                                className="flex-1"
                                onClick={() => router.push(`/view-drawer/${drawer.id}`)}
                              >
                                View
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </>
            )}
            
            {activeMenu === 'settings' && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Account Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Username</label>
                        <div className="mt-1 p-2 border rounded-md bg-gray-50">{user?.username}</div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-700">Email</label>
                        <div className="mt-1 p-2 border rounded-md bg-gray-50">{user?.email}</div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-700">First Name</label>
                        <div className="mt-1 p-2 border rounded-md bg-gray-50">{user?.first_name || "-"}</div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-700">Last Name</label>
                        <div className="mt-1 p-2 border rounded-md bg-gray-50">{user?.last_name || "-"}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Application Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm text-gray-500 mb-4">
                          Configure default dimensions and appearance settings.
                        </p>
                        <Button onClick={() => router.push('/profile/settings')} className="w-full">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                          </svg>
                          Application Settings
                        </Button>
                      </div>
                    </div>
                    <Button variant="outline" onClick={() => router.push('/profile/password')} className="w-full">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      Change Password
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}