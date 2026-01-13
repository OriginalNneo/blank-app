'use client';

import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { SOAItem, SOARequest, ReceiptProcessingResponse } from '@/types';
import { soaService } from '@/services/api';
import {
  PlusIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  CloudArrowUpIcon,
  PhotoIcon,
  XMarkIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

export default function SOAPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [eventName, setEventName] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [venue, setVenue] = useState('Teck Ghee CC');
  const [activityCode, setActivityCode] = useState('');
  const [preparedBy, setPreparedBy] = useState(user?.username || '');
  const [designationPrepared, setDesignationPrepared] = useState('Member');
  const [certifiedBy, setCertifiedBy] = useState('');
  const [designationCertified, setDesignationCertified] = useState('Chairman/Treasurer');

  // Data tables
  const [incomeItems, setIncomeItems] = useState<SOAItem[]>([
    { Description: 'Participant Fees', "Actual ($)": 0, "Budgeted ($)": 0, "Variance ($)": 0 }
  ]);
  const [expenseItems, setExpenseItems] = useState<SOAItem[]>([
    { Description: 'Food & Bev', "Actual ($)": 0, "Budgeted ($)": 0, "Variance ($)": 0 }
  ]);

  // Receipt processing
  const [uploadedFiles, setUploadedFiles] = useState<FileList | null>(null);
  const [isProcessingReceipts, setIsProcessingReceipts] = useState(false);
  const [receiptResults, setReceiptResults] = useState<ReceiptProcessingResponse | null>(null);

  // UI state
  const [isGenerating, setIsGenerating] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  const calculateVariance = (actual: number, budgeted: number) => {
    return actual - budgeted;
  };

  const calculateTotal = (items: SOAItem[], field: keyof SOAItem) => {
    return items.reduce((sum, item) => sum + (item[field] as number), 0);
  };

  const updateIncomeItem = (index: number, field: keyof SOAItem, value: any) => {
    const updatedItems = [...incomeItems];
    updatedItems[index] = { ...updatedItems[index], [field]: value };

    // Recalculate variance if actual or budgeted changed
    if (field === 'Actual ($)' || field === 'Budgeted ($)') {
      updatedItems[index]['Variance ($)'] = calculateVariance(
        updatedItems[index]['Actual ($)'],
        updatedItems[index]['Budgeted ($)']
      );
    }

    setIncomeItems(updatedItems);
  };

  const updateExpenseItem = (index: number, field: keyof SOAItem, value: any) => {
    const updatedItems = [...expenseItems];
    updatedItems[index] = { ...updatedItems[index], [field]: value };

    // Recalculate variance if actual or budgeted changed
    if (field === 'Actual ($)' || field === 'Budgeted ($)') {
      updatedItems[index]['Variance ($)'] = calculateVariance(
        updatedItems[index]['Actual ($)'],
        updatedItems[index]['Budgeted ($)']
      );
    }

    setExpenseItems(updatedItems);
  };

  const addIncomeItem = () => {
    setIncomeItems([...incomeItems, { Description: '', "Actual ($)": 0, "Budgeted ($)": 0, "Variance ($)": 0 }]);
  };

  const addExpenseItem = () => {
    setExpenseItems([...expenseItems, { Description: '', "Actual ($)": 0, "Budgeted ($)": 0, "Variance ($)": 0 }]);
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

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      setUploadedFiles(files);
    }
  };

  const handleProcessReceipts = async () => {
    if (!uploadedFiles || uploadedFiles.length === 0) {
      alert('Please select receipt files first');
      return;
    }

    setIsProcessingReceipts(true);
    try {
      const results = await soaService.processReceipts(uploadedFiles);
      setReceiptResults(results);

      // Add processed items to tables
      if (results.income_items && results.income_items.length > 0) {
        const newIncomeItems = results.income_items.map((item: any) => ({
          Description: item.Description,
          "Actual ($)": item["Actual ($)"],
          "Budgeted ($)": item["Budgeted ($)"],
          "Variance ($)": calculateVariance(item["Actual ($)"], item["Budgeted ($)"])
        }));
        setIncomeItems([...incomeItems, ...newIncomeItems]);
      }

      if (results.expenditure_items && results.expenditure_items.length > 0) {
        const newExpenseItems = results.expenditure_items.map((item: any) => ({
          Description: item.Description,
          "Actual ($)": item["Actual ($)"],
          "Budgeted ($)": item["Budgeted ($)"],
          "Variance ($)": calculateVariance(item["Actual ($)"], item["Budgeted ($)"])
        }));
        setExpenseItems([...expenseItems, ...newExpenseItems]);
      }

      alert(`Successfully processed ${results.processed_receipts} receipts and added items to tables!`);
    } catch (error) {
      console.error('Receipt processing error:', error);
      alert('Error processing receipts. Please try again.');
    } finally {
      setIsProcessingReceipts(false);
    }
  };

  const handlePreview = async () => {
    if (!eventName.trim()) {
      alert('Please enter an event name');
      return;
    }

    try {
      const soaData: SOARequest = {
        event_name: eventName,
        event_date: eventDate,
        venue,
        activity_code: activityCode,
        income_items: incomeItems,
        expense_items: expenseItems,
        prepared_by: preparedBy,
        designation_prepared: designationPrepared,
        certified_by: certifiedBy,
        designation_certified: designationCertified,
      };

      const result = await soaService.previewSOA(soaData);
      setPreviewData(result);
      setShowPreview(true);
    } catch (error) {
      console.error('Preview error:', error);
      alert('Error generating preview');
    }
  };

  const handleGenerate = async () => {
    if (!eventName.trim()) {
      alert('Please enter an event name');
      return;
    }

    setIsGenerating(true);
    try {
      const soaData: SOARequest = {
        event_name: eventName,
        event_date: eventDate,
        venue,
        activity_code: activityCode,
        income_items: incomeItems,
        expense_items: expenseItems,
        prepared_by: preparedBy,
        designation_prepared: designationPrepared,
        certified_by: certifiedBy,
        designation_certified: designationCertified,
      };

      const blob = await soaService.generateSOA(soaData);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${eventName}_SOA.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Generation error:', error);
      alert('Error generating SOA');
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
      const soaData: SOARequest = {
        event_name: eventName,
        event_date: eventDate,
        venue,
        activity_code: activityCode,
        income_items: incomeItems,
        expense_items: expenseItems,
        prepared_by: preparedBy,
        designation_prepared: designationPrepared,
        certified_by: certifiedBy,
        designation_certified: designationCertified,
      };

      await soaService.sendToTelegram(soaData);
      alert('SOA document and approval poll sent to Telegram successfully!');
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
            <h1 className="text-3xl font-bold text-black mb-2">Statement of Accounts (SOA)</h1>
            <p className="text-black opacity-90">Generate professional SOA reports with receipt processing</p>
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
                <input
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Venue</label>
                <input
                  type="text"
                  value={venue}
                  onChange={(e) => setVenue(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Activity Code</label>
                <input
                  type="text"
                  value={activityCode}
                  onChange={(e) => setActivityCode(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="A1234567"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-6">
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
                <label className="block text-sm font-medium text-white mb-2">Designation (Prep)</label>
                <input
                  type="text"
                  value={designationPrepared}
                  onChange={(e) => setDesignationPrepared(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Certified By</label>
                <input
                  type="text"
                  value={certifiedBy}
                  onChange={(e) => setCertifiedBy(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Designation (Cert)</label>
                <input
                  type="text"
                  value={designationCertified}
                  onChange={(e) => setDesignationCertified(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                />
              </div>
            </div>
          </div>

          {/* Receipt Processing Section */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <h2 className="text-xl font-semibold text-white mb-6">Receipt Processing</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Upload Receipt Images
                </label>
                <div className="flex items-center space-x-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-black bg-white bg-opacity-20 hover:bg-opacity-30"
                  >
                    <PhotoIcon className="h-5 w-5 mr-2" />
                    Choose Files
                  </button>
                  {uploadedFiles && (
                    <span className="text-sm text-white opacity-90">
                      {uploadedFiles.length} file(s) selected
                    </span>
                  )}
                </div>
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={handleProcessReceipts}
                  disabled={!uploadedFiles || isProcessingReceipts}
                  className="inline-flex items-center px-4 py-2 text-white text-sm font-medium rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed" style={{ backgroundColor: '#F08C21' }}
                >
                  <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                  {isProcessingReceipts ? 'Processing...' : 'Process Receipts with AI'}
                </button>
              </div>
            </div>

            {receiptResults && (
              <div className="mt-6 p-4 border border-green-200 rounded-md" style={{ backgroundColor: '#B4B534' }}>
                <h3 className="text-sm font-medium text-white mb-2">Processing Results</h3>
                <p className="text-sm text-white">
                  Successfully processed {receiptResults.processed_receipts} receipts.
                  Added {receiptResults.income_items.length} income items and {receiptResults.expenditure_items.length} expense items.
                </p>
              </div>
            )}
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Actual ($)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Budgeted ($)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Variance ($)</th>
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
                          value={item['Actual ($)']}
                          onChange={(e) => updateIncomeItem(index, 'Actual ($)', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          step="0.01"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          value={item['Budgeted ($)']}
                          onChange={(e) => updateIncomeItem(index, 'Budgeted ($)', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          step="0.01"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">
                        ${item['Variance ($)'].toFixed(2)}
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
                    <td colSpan={1} className="px-6 py-4 text-sm font-medium text-white">Total Income</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(incomeItems, 'Actual ($)').toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(incomeItems, 'Budgeted ($)').toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(incomeItems, 'Variance ($)').toFixed(2)}
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
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Actual ($)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Budgeted ($)</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase tracking-wider">Variance ($)</th>
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
                          value={item['Actual ($)']}
                          onChange={(e) => updateExpenseItem(index, 'Actual ($)', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          step="0.01"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <input
                          type="number"
                          value={item['Budgeted ($)']}
                          onChange={(e) => updateExpenseItem(index, 'Budgeted ($)', Number(e.target.value))}
                          className="w-full px-2 py-1 border border-gray-300 rounded"
                          step="0.01"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">
                        ${item['Variance ($)'].toFixed(2)}
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
                    <td colSpan={1} className="px-6 py-4 text-sm font-medium text-white">Total Expenditure</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(expenseItems, 'Actual ($)').toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(expenseItems, 'Budgeted ($)').toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-white">
                      ${calculateTotal(expenseItems, 'Variance ($)').toFixed(2)}
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
                <p className="text-sm text-green-600 font-medium">Total Income (Actual)</p>
                <p className="text-2xl font-bold text-green-800">${calculateTotal(incomeItems, 'Actual ($)').toFixed(2)}</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-red-600 font-medium">Total Expenditure (Actual)</p>
                <p className="text-2xl font-bold text-red-800">${calculateTotal(expenseItems, 'Actual ($)').toFixed(2)}</p>
              </div>
              <div className={`text-center p-4 rounded-lg ${
                calculateTotal(incomeItems, 'Actual ($)') - calculateTotal(expenseItems, 'Actual ($)') >= 0
                  ? 'bg-blue-50' : 'bg-orange-50'
              }`}>
                <p className={`text-sm font-medium ${
                  calculateTotal(incomeItems, 'Actual ($)') - calculateTotal(expenseItems, 'Actual ($)') >= 0
                    ? 'text-blue-600' : 'text-orange-600'
                }`}>
                  Net {calculateTotal(incomeItems, 'Actual ($)') - calculateTotal(expenseItems, 'Actual ($)') >= 0 ? 'Surplus' : 'Deficit'}
                </p>
                <p className={`text-2xl font-bold ${
                  calculateTotal(incomeItems, 'Actual ($)') - calculateTotal(expenseItems, 'Actual ($)') >= 0
                    ? 'text-blue-800' : 'text-orange-800'
                }`}>
                  ${(calculateTotal(incomeItems, 'Actual ($)') - calculateTotal(expenseItems, 'Actual ($)')).toFixed(2)}
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
              className="inline-flex items-center px-6 py-3 text-white text-sm font-medium rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed" style={{ backgroundColor: '#F08C21' }}
            >
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
              {isGenerating ? 'Generating...' : 'Generate SOA'}
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
                <h3 className="text-lg font-semibold text-white">SOA Preview</h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              <div className="space-y-2">
                <p><strong>Total Income (Actual):</strong> ${previewData.income_total.toFixed(2)}</p>
                <p><strong>Total Expenditure (Actual):</strong> ${previewData.expense_total.toFixed(2)}</p>
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