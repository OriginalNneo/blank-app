'use client';

import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { minutesService } from '@/services/api';
import { ArrowDownTrayIcon, DocumentArrowUpIcon, EyeIcon, XMarkIcon, CalendarIcon, ClockIcon } from '@heroicons/react/24/outline';

export default function MinutesPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Form state
  const [meetingTitle, setMeetingTitle] = useState('Corporate Board Meeting');
  const [meetingDate, setMeetingDate] = useState('');
  const [meetingTime, setMeetingTime] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [attendees, setAttendees] = useState('');
  const [absent, setAbsent] = useState('');
  const [meetingChair, setMeetingChair] = useState('');

  // Refs for date inputs
  const dateInputRef = useRef<HTMLInputElement>(null);

  // File state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.name.toLowerCase().endsWith('.pptx') || file.name.toLowerCase().endsWith('.ppt')) {
        setSelectedFile(file);
      } else {
        alert('Please select a PowerPoint file (.pptx or .ppt)');
        event.target.value = '';
      }
    }
  };

  const handlePreview = async () => {
    if (!selectedFile) {
      alert('Please select a PowerPoint file first');
      return;
    }

    setIsPreviewing(true);
    try {
      // Combine date and time for the API
      const dateTime = meetingDate && meetingTime ? `${meetingDate}T${meetingTime}` : (meetingDate || '');
      const result = await minutesService.previewMinutes(
        selectedFile,
        meetingTitle,
        dateTime,
        company,
        location
      );
      setPreviewData(result);
      setShowPreview(true);
    } catch (error) {
      console.error('Preview error:', error);
      alert('Error previewing PowerPoint content');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleGenerate = async () => {
    if (!selectedFile) {
      alert('Please select a PowerPoint file first');
      return;
    }

    setIsGenerating(true);
    try {
      // Combine date and time for the API
      const dateTime = meetingDate && meetingTime ? `${meetingDate}T${meetingTime}` : (meetingDate || '');
      const blob = await minutesService.generateMinutes(
        selectedFile,
        meetingTitle,
        dateTime,
        company,
        location,
        attendees,
        absent,
        meetingChair
      );

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${meetingTitle.replace(/\s+/g, '_')}_Minutes.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Generation error:', error);
      alert('Error generating meeting minutes');
    } finally {
      setIsGenerating(false);
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
            <h1 className="text-3xl font-bold text-black mb-2">Meeting Minutes Generator</h1>
            <p className="text-black opacity-90">
              Upload a PowerPoint presentation to automatically generate standardized meeting minutes
            </p>
          </div>

          {/* File Upload Section */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <h2 className="text-xl font-semibold text-white mb-6">Upload PowerPoint</h2>
            <div className="mb-6">
              <label className="block text-sm font-medium text-white mb-2">
                Select PowerPoint File (.pptx or .ppt)
              </label>
              <div className="flex items-center space-x-4">
                <label className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-black bg-white hover:bg-gray-50 cursor-pointer">
                  <DocumentArrowUpIcon className="h-4 w-4 mr-2" />
                  <span>{selectedFile ? 'Change File' : 'Choose File'}</span>
                  <input
                    type="file"
                    accept=".pptx,.ppt,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.ms-powerpoint"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
                {selectedFile && (
                  <span className="text-sm text-white opacity-90">
                    Selected: {selectedFile.name}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Meeting Information Section */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <h2 className="text-xl font-semibold text-white mb-6">Meeting Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Meeting Title</label>
                <input
                  type="text"
                  value={meetingTitle}
                  onChange={(e) => setMeetingTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Corporate Board Meeting"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Date</label>
                <div className="relative">
                  <input
                    ref={dateInputRef}
                    type="date"
                    value={meetingDate}
                    onChange={(e) => setMeetingDate(e.target.value)}
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
                <label className="block text-sm font-medium text-white mb-2">Time Begins</label>
                <div className="relative">
                  <input
                    type="time"
                    value={meetingTime}
                    onChange={(e) => setMeetingTime(e.target.value)}
                    className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  />
                  <ClockIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Company</label>
                <input
                  type="text"
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Teck Ghee Youth Network"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Meeting room or venue"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Attendees</label>
                <input
                  type="text"
                  value={attendees}
                  onChange={(e) => setAttendees(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Names of attendees"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Absent</label>
                <input
                  type="text"
                  value={absent}
                  onChange={(e) => setAbsent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Names of absent members"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Meeting Chair</label>
                <input
                  type="text"
                  value={meetingChair}
                  onChange={(e) => setMeetingChair(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                  placeholder="Chairperson name"
                />
              </div>
            </div>
            <div className="mt-4 p-4 bg-blue-50 rounded-md">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Information will be extracted from the PowerPoint presentation using AI. 
                You can fill in additional details above or leave them blank to be filled in later.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={handlePreview}
              disabled={!selectedFile || isPreviewing}
              className="inline-flex items-center px-6 py-3 text-white text-sm font-medium rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#F08C21' }}
            >
              <EyeIcon className="h-4 w-4 mr-2" />
              {isPreviewing ? 'Previewing...' : 'Preview Content'}
            </button>
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !selectedFile}
              className="inline-flex items-center px-6 py-3 bg-cyan-600 text-white text-sm font-medium rounded-md hover:bg-cyan-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
              {isGenerating ? 'Generating...' : 'Generate Minutes'}
            </button>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Extracted Content Preview</h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              {previewData.extracted_data && (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Meeting Title:</h4>
                    <p className="text-gray-700">{previewData.extracted_data.meeting_title || 'Not found'}</p>
                  </div>
                  
                  {previewData.extracted_data.agenda_items && previewData.extracted_data.agenda_items.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Agenda Items:</h4>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        {previewData.extracted_data.agenda_items.map((item: any, index: number) => (
                          <li key={index}>
                            <strong>{item.title}</strong>
                            {item.description && <span className="ml-2">- {item.description.substring(0, 100)}...</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {previewData.extracted_data.extracted_date && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Extracted Date:</h4>
                      <p className="text-gray-700">{previewData.extracted_data.extracted_date}</p>
                    </div>
                  )}
                  
                  {previewData.extracted_data.extracted_location && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Extracted Location:</h4>
                      <p className="text-gray-700">{previewData.extracted_data.extracted_location}</p>
                    </div>
                  )}
                </div>
              )}
              
              <div className="mt-6 flex justify-end">
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
