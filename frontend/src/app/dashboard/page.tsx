'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { CalculatorIcon, DocumentTextIcon, ChartBarIcon } from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const quickActions = [
    {
      name: 'Budget Planner',
      description: 'Create event budget templates',
      href: '/dashboard/budget',
      icon: CalculatorIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'SOA Generator',
      description: 'Generate Statement of Accounts',
      href: '/dashboard/soa',
      icon: DocumentTextIcon,
      color: 'bg-green-500',
    },
  ];

  return (
    <DashboardLayout>
      <div className="p-4 lg:p-6 bg-white min-h-screen">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-2xl lg:text-3xl font-bold text-black mb-1">
              Welcome back, {user.username}!
            </h1>
            <p className="text-gray-600 text-sm lg:text-base">
              Teck Ghee Youth Network Administration Portal
            </p>
          </div>

          {/* Quick Actions */}
          <div className="mb-6">
            <h2 className="text-lg lg:text-xl font-semibold text-gray-900 mb-3 lg:mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {quickActions.map((action) => (
                <div
                  key={action.name}
                  onClick={() => router.push(action.href)}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer group"
                >
                  <div className="flex items-center mb-4">
                    <div className={`p-3 rounded-lg ${action.color} mr-4`}>
                      <action.icon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-cyan-600 transition-colors">
                        {action.name}
                      </h3>
                    </div>
                  </div>
                  <p className="text-gray-600">{action.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-cyan-100 rounded-lg">
                  <CalculatorIcon className="h-6 w-6 text-cyan-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Budgets Created</p>
                  <p className="text-2xl font-bold text-gray-900">0</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <DocumentTextIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">SOAs Generated</p>
                  <p className="text-2xl font-bold text-gray-900">0</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <ChartBarIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Receipts Processed</p>
                  <p className="text-2xl font-bold text-gray-900">0</p>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 lg:p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <div className="text-center py-8 text-gray-500">
              <p>No recent activity yet.</p>
              <p className="text-sm">Start by creating your first budget or SOA.</p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}