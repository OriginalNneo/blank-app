'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  HomeIcon,
  DocumentTextIcon,
  CalculatorIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [topBarVisible, setTopBarVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down - hide top bar
        setTopBarVisible(false);
      } else if (currentScrollY < lastScrollY) {
        // Scrolling up - show top bar
        setTopBarVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
    { name: 'Budget Planner', href: '/dashboard/budget', icon: CalculatorIcon },
    { name: 'SOA', href: '/dashboard/soa', icon: DocumentTextIcon },
  ];

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <>
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-25" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 bg-white shadow-lg transform transition-all duration-300 ease-in-out ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      } ${
        sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'
      }`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className={`flex items-center justify-center h-16 px-4 ${
            sidebarCollapsed ? 'lg:justify-center' : 'lg:justify-start'
          }`} style={{ backgroundColor: '#6698CC' }}>
            <h1 className={`font-bold text-white transition-all duration-300 ${
              sidebarCollapsed ? 'text-sm lg:text-xs' : 'text-xl'
            }`}>
              {sidebarCollapsed ? 'TA' : 'TGYN Admin'}
            </h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <button
                  key={item.name}
                  onClick={() => {
                    // Navigate to the page
                    router.push(item.href);
                    // Close mobile sidebar
                    setSidebarOpen(false);
                    // Collapse desktop sidebar
                    setSidebarCollapsed(true);
                  }}
                  className={`flex items-center w-full px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 ${
                    sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''
                  } ${
                    isActive
                      ? 'bg-cyan-50 text-cyan-700 border-r-2 border-cyan-500'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                  title={sidebarCollapsed ? item.name : undefined}
                >
                  <item.icon className={`h-5 w-5 ${sidebarCollapsed ? 'lg:mr-0' : 'mr-3'}`} />
                  <span className={`transition-opacity duration-300 ${
                    sidebarCollapsed ? 'lg:hidden lg:opacity-0' : 'lg:opacity-100'
                  }`}>
                    {item.name}
                  </span>
                </button>
              );
            })}
          </nav>

          {/* User info and logout */}
          <div className="p-4 border-t border-gray-200">
            {/* Collapse toggle button for desktop */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden lg:flex items-center justify-center w-full mb-4 p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors duration-200"
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <Bars3Icon className={`h-5 w-5 transform transition-transform duration-300 ${
                sidebarCollapsed ? 'rotate-90' : ''
              }`} />
            </button>

            <div className={`flex items-center mb-4 ${
              sidebarCollapsed ? 'lg:justify-center' : ''
            }`}>
              <div className="flex-shrink-0">
                <div className="h-8 w-8 rounded-full bg-cyan-500 flex items-center justify-center">
                  <span className="text-sm font-medium text-white">
                    {user?.username?.charAt(0).toUpperCase()}
                  </span>
                </div>
              </div>
              <div className={`ml-3 transition-opacity duration-300 ${
                sidebarCollapsed ? 'lg:hidden lg:opacity-0' : 'lg:opacity-100'
              }`}>
                <p className="text-sm font-medium text-gray-700">{user?.username}</p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className={`flex items-center w-full px-4 py-2 text-sm font-medium text-gray-600 rounded-lg hover:bg-gray-50 hover:text-gray-900 transition-all duration-200 ${
                sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''
              }`}
              title={sidebarCollapsed ? "Logout" : undefined}
            >
              <ArrowRightOnRectangleIcon className={`h-5 w-5 ${sidebarCollapsed ? 'lg:mr-0' : 'mr-3'}`} />
              <span className={`transition-opacity duration-300 ${
                sidebarCollapsed ? 'lg:hidden lg:opacity-0' : 'lg:opacity-100'
              }`}>
                Logout
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-25" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <div className={`min-h-screen bg-white transition-all duration-300 ${
        sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'
      }`}>
        {/* Top bar */}
        <div className={`sticky top-0 z-10 bg-white border-b border-gray-200 transition-transform duration-300 ${
          topBarVisible ? 'translate-y-0' : '-translate-y-full'
        }`}>
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 lg:hidden"
              >
                <Bars3Icon className="h-6 w-6" />
              </button>
              {/* Desktop sidebar toggle */}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="hidden lg:block p-2 ml-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
                title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
              >
                <Bars3Icon className={`h-6 w-6 transform transition-transform duration-300 ${
                  sidebarCollapsed ? 'rotate-180' : ''
                }`} />
              </button>
            </div>
            <h1 className="text-lg font-semibold text-gray-900">TGYN Admin Portal</h1>
            <div className="w-10" /> {/* Spacer */}
          </div>
        </div>

        {/* Page content */}
        <main className="bg-gray-50 min-h-screen relative z-0 text-gray-900">
          {children}
        </main>
      </div>
    </>
  );
}