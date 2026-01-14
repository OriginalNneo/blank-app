'use client';

import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { BudgetItem, BudgetRequest } from '@/types';
import { budgetService } from '@/services/api';
import { PlusIcon, TrashIcon, ArrowDownTrayIcon, EyeIcon, DocumentTextIcon, XMarkIcon, CalendarIcon } from '@heroicons/react/24/outline';

export default function BudgetPlannerPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Form state
  const [eventName, setEventName] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [participants, setParticipants] = useState(0);
  const [volunteers, setVolunteers] = useState(0);
  const [preparedBy, setPreparedBy] = useState(user?.username || '');
  const [designation, setDesignation] = useState(user?.role || 'Member');
  const [vettedBy, setVettedBy] = useState('');

  // Data tables
  const [incomeItems, setIncomeItems] = useState<BudgetItem[]>([
    { Description: 'Fees', "Qty": 0, "$ per unit": 0, "$ (Total)": 0 }
  ]);
  const [expenseItems, setExpenseItems] = useState<BudgetItem[]>([
    { Description: 'Food', "Qty": 0, "$ per unit": 0, "$ (Total)": 0 }
  ]);

  // UI state
  const [isGenerating, setIsGenerating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importedFileName, setImportedFileName] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);

  // Refs for date inputs
  const dateInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  // Keep Prepared By / Designation in sync with logged-in user on first load
  useEffect(() => {
    if (user) {
      setPreparedBy((prev) => prev || user.username);
      setDesignation((prev) => (prev === 'Member' || !prev ? user.role : prev));
    }
  }, [user]);

  const calculateTotal = (items: BudgetItem[]) => {
    return items.reduce((sum, item) => sum + item['$ (Total)'], 0);
  };

  const updateIncomeItem = (index: number, field: keyof BudgetItem, value: any) => {
    const updatedItems = [...incomeItems];
    updatedItems[index] = { ...updatedItems[index], [field]: value };

    // Recalculate total if qty or unit price changed
    if (field === 'Qty' || field === '$ per unit') {
      updatedItems[index]['$ (Total)'] = updatedItems[index]['Qty'] * updatedItems[index]['$ per unit'];
    }

    setIncomeItems(updatedItems);
  };

  const updateExpenseItem = (index: number, field: keyof BudgetItem, value: any) => {
    const updatedItems = [...expenseItems];
    updatedItems[index] = { ...updatedItems[index], [field]: value };

    // Recalculate total if qty or unit price changed
    if (field === 'Qty' || field === '$ per unit') {
      updatedItems[index]['$ (Total)'] = updatedItems[index]['Qty'] * updatedItems[index]['$ per unit'];
    }

    setExpenseItems(updatedItems);
  };

  const addIncomeItem = () => {
    setIncomeItems([...incomeItems, { Description: '', "Qty": 0, "$ per unit": 0, "$ (Total)": 0 }]);
  };

  const addExpenseItem = () => {
    setExpenseItems([...expenseItems, { Description: '', "Qty": 0, "$ per unit": 0, "$ (Total)": 0 }]);
  };

  const removeIncomeItem = (index: number) => {
    if (incomeItems.length > 1) {
      setIncomeItems(incomeItems.filter((_, i) => i !== index));
    }
  };

  const removeExpenseItem = (index: number) => {
    if (expenseItems.length > 1) {
      setExpenseItems(expenseItems.filter((_, i) => i !== index));
    }
  };

  const handlePreview = async () => {
    if (!eventName.trim()) {
      alert('Please enter an event name');
      return;
    }

    try {
      const budgetData: BudgetRequest = {
        event_name: eventName,
        event_date: eventDate,
        participants,
        volunteers,
        income_items: incomeItems,
        expense_items: expenseItems,
        prepared_by: preparedBy,
        designation,
        vetted_by: vettedBy,
      };

      const result = await budgetService.previewBudget(budgetData);
      setPreviewData(result);
      setShowPreview(true);
    } catch (error) {
      console.error('Preview error:', error);
      alert('Error generating preview');
    }
  };

  const handleImportExisting = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setImportedFileName(file.name);
    try {
      const result = await budgetService.importExistingBudget(file);

      // Basic event details (fallbacks if missing)
      if (result.event_name) setEventName(result.event_name);
      if (result.event_date) setEventDate(result.event_date);
      if (typeof result.participants === 'number') setParticipants(result.participants);
      if (typeof result.volunteers === 'number') setVolunteers(result.volunteers);

      if (result.prepared_by) setPreparedBy(result.prepared_by);
      if (result.designation) setDesignation(result.designation);
      if (result.vetted_by) setVettedBy(result.vetted_by);

      // Tables
      if (Array.isArray(result.income_items) && result.income_items.length > 0) {
        setIncomeItems(result.income_items);
      }
      if (Array.isArray(result.expense_items) && result.expense_items.length > 0) {
        setExpenseItems(result.expense_items);
      }

      alert('Existing budget Excel imported successfully. You can now modify and regenerate.');
    } catch (error) {
      console.error('Import error:', error);
      alert('Error importing existing budget file. Please ensure it was generated by this system.');
    } finally {
      setIsImporting(false);
      // Reset input so same file can be selected again if needed
      event.target.value = '';
    }
  };

  const handleGenerate = async () => {
    if (!eventName.trim()) {
      alert('Please enter an event name');
      return;
    }

    setIsGenerating(true);
    try {
      const budgetData: BudgetRequest = {
        event_name: eventName,
        event_date: eventDate,
        participants,
        volunteers,
        income_items: incomeItems,
        expense_items: expenseItems,
        prepared_by: preparedBy,
        designation,
        vetted_by: vettedBy,
      };

      const blob = await budgetService.generateBudget(budgetData);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${eventName}_Budget.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Generation error:', error);
      alert('Error generating budget');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendToTelegram = async () => {
    if (!eventName.trim()) {
      alert('Please enter an event name');
      return;
    }

    try {
      const budgetData: BudgetRequest = {
        event_name: eventName,
        event_date: eventDate,
        participants,
        volunteers,
        income_items: incomeItems,
        expense_items: expenseItems,
        prepared_by: preparedBy,
        designation,
        vetted_by: vettedBy,
      };

      await budgetService.sendToTelegram(budgetData);
      alert('Budget document and approval poll sent to Telegram successfully!');
    } catch (error) {
      console.error('Telegram error:', error);
      alert('Error sending to Telegram');
    }
  };

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

  return (
    <DashboardLayout>
      <div className="p-4 lg:p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-black mb-2">Budget Planner</h1>
            <p className="text-black opacity-90">Create professional event budget templates</p>
          </div>

          {/* Form */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <h2 className="text-xl font-semibold text-white mb-6">Event Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Event Name *</label>
                <input
                  type="text"
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Enter event name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Event Date</label>
                <div className="relative">
                  <input
                    ref={dateInputRef}
                    type="date"
                    value={eventDate}
                    onChange={(e) => setEventDate(e.target.value)}
                    className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      if (dateInputRef.current) {
                        dateInputRef.current.focus();
                        if ('showPicker' in dateInputRef.current) {
                          (dateInputRef.current as any).showPicker();
                        } else {
                          dateInputRef.current.click();
                        }
                      }
                    }}
                    className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 hover:text-gray-600 cursor-pointer focus:outline-none"
                    aria-label="Open calendar"
                  >
                    <CalendarIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Participants</label>
                <input
                  type="number"
                  value={participants}
                  onChange={(e) => setParticipants(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Volunteers</label>
                <input
                  type="number"
                  value={volunteers}
                  onChange={(e) => setVolunteers(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  min="0"
                />
              </div>
            </div>

            {/* Import Existing Budget Section */}
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-white mb-3">Modify Existing Budget Excel</h3>
              <p className="text-sm text-white opacity-90 mb-3">
                Choose an existing budget Excel file (generated from this tool) to load and modify.
              </p>
              <div className="flex items-center space-x-4">
                <label className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-black bg-white bg-opacity-20 hover:bg-opacity-30 cursor-pointer">
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  <span>{isImporting ? 'Importing...' : 'Choose Budget File'}</span>
                  <input
                    type="file"
                    accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    onChange={handleImportExisting}
                    className="hidden"
                  />
                </label>
                {importedFileName && (
                  <span className="text-sm text-white opacity-90">
                    Loaded: {importedFileName}
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Prepared By</label>
                <input
                  type="text"
                  value={preparedBy}
                  onChange={(e) => setPreparedBy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Designation</label>
                <input
                  type="text"
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Vetted By</label>
                <input
                  type="text"
                  value={vettedBy}
                  onChange={(e) => setVettedBy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
            </div>
          </div>

          {/* Income Table */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Income</h2>
              <button
                onClick={addIncomeItem}
                className="inline-flex items-center px-4 py-2 text-white text-sm font-medium rounded-md hover:opacity-90" style={{ backgroundColor: '#F08C21' }}
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Item
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead style={{ backgroundColor: '#B4B534' }}>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">$ per unit</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Qty</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">$ (Total)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {incomeItems.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="text"
                          value={item.Description}
                          onChange={(e) => updateIncomeItem(index, 'Description', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          value={item['$ per unit']}
                          onChange={(e) => updateIncomeItem(index, '$ per unit', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          step="0.01"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          value={item.Qty}
                          onChange={(e) => updateIncomeItem(index, 'Qty', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">
                        ${item['$ (Total)'].toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => removeIncomeItem(index)}
                          disabled={incomeItems.length === 1}
                          className="text-red-600 hover:text-red-900 disabled:text-gray-400"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  <tr style={{ backgroundColor: '#B4B534' }}>
                    <td colSpan={3} className="px-6 py-4 text-sm font-medium text-white">Total Income</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(incomeItems).toFixed(2)}
                    </td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Expense Table */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white">Expenditure</h2>
              <button
                onClick={addExpenseItem}
                className="inline-flex items-center px-4 py-2 text-white text-sm font-medium rounded-md hover:opacity-90" style={{ backgroundColor: '#F08C21' }}
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Item
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead style={{ backgroundColor: '#B4B534' }}>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Description</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">$ per unit</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Qty</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">$ (Total)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {expenseItems.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="text"
                          value={item.Description}
                          onChange={(e) => updateExpenseItem(index, 'Description', e.target.value)}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          value={item['$ per unit']}
                          onChange={(e) => updateExpenseItem(index, '$ per unit', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          step="0.01"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          value={item.Qty}
                          onChange={(e) => updateExpenseItem(index, 'Qty', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">
                        ${item['$ (Total)'].toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => removeExpenseItem(index)}
                          disabled={expenseItems.length === 1}
                          className="text-red-600 hover:text-red-900 disabled:text-gray-400"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  <tr style={{ backgroundColor: '#B4B534' }}>
                    <td colSpan={3} className="px-6 py-4 text-sm font-medium text-white">Total Expenditure</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(expenseItems).toFixed(2)}
                    </td>
                    <td></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Summary */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <h2 className="text-xl font-semibold text-white mb-4">Summary</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600 font-medium">Total Income</p>
                <p className="text-2xl font-bold text-green-800">${calculateTotal(incomeItems).toFixed(2)}</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-red-600 font-medium">Total Expenditure</p>
                <p className="text-2xl font-bold text-red-800">${calculateTotal(expenseItems).toFixed(2)}</p>
              </div>
              <div className={`text-center p-4 rounded-lg ${calculateTotal(incomeItems) - calculateTotal(expenseItems) >= 0 ? 'bg-blue-50' : 'bg-orange-50'}`}>
                <p className={`text-sm font-medium ${calculateTotal(incomeItems) - calculateTotal(expenseItems) >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                  Net {calculateTotal(incomeItems) - calculateTotal(expenseItems) >= 0 ? 'Surplus' : 'Deficit'}
                </p>
                <p className={`text-2xl font-bold ${calculateTotal(incomeItems) - calculateTotal(expenseItems) >= 0 ? 'text-blue-800' : 'text-orange-800'}`}>
                  ${(calculateTotal(incomeItems) - calculateTotal(expenseItems)).toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={handlePreview}
              className="inline-flex items-center px-6 py-3 text-white text-sm font-medium rounded-md hover:opacity-90" style={{ backgroundColor: '#F08C21' }}
            >
              <EyeIcon className="h-4 w-4 mr-2" />
              Preview
            </button>
            <button
              onClick={handleSendToTelegram}
              className="inline-flex items-center px-6 py-3 text-white text-sm font-medium rounded-md hover:opacity-90" style={{ backgroundColor: '#F08C21' }}
            >
              <DocumentTextIcon className="h-4 w-4 mr-2" />
              Send to Telegram
            </button>
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !eventName.trim()}
              className="inline-flex items-center px-6 py-3 bg-cyan-600 text-white text-sm font-medium rounded-md hover:bg-cyan-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
              {isGenerating ? 'Generating...' : 'Generate Budget'}
            </button>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Budget Preview</h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-2">
                <p><strong>Total Income:</strong> ${previewData.income_total.toFixed(2)}</p>
                <p><strong>Total Expenditure:</strong> ${previewData.expense_total.toFixed(2)}</p>
                <p><strong>Net Amount:</strong> ${previewData.net_amount.toFixed(2)}</p>
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => setShowPreview(false)}
                  className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}