'use client';

import { useState, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { minutesService } from '@/services/api';
import { ArrowDownTrayIcon, EyeIcon, XMarkIcon, CalendarIcon, ClockIcon } from '@heroicons/react/24/outline';

export default function MinutesPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Form state
  const [meetingContent, setMeetingContent] = useState('');
  const [meetingTitle, setMeetingTitle] = useState('Corporate Board Meeting');
  const [meetingDate, setMeetingDate] = useState('');
  const [meetingTime, setMeetingTime] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [attendees, setAttendees] = useState('');
  const [absent, setAbsent] = useState('');
  const [meetingChair, setMeetingChair] = useState('');

  // Attendance state
  const [members, setMembers] = useState<Array<{name: string, address: string}>>([]);
  const [attendance, setAttendance] = useState<Record<string, string>>({});
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [isSubmittingAttendance, setIsSubmittingAttendance] = useState(false);

  // Refs for date inputs
  const dateInputRef = useRef<HTMLInputElement>(null);

  // State
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    // Load members when component mounts
    const loadMembers = async () => {
      setIsLoadingMembers(true);
      try {
        const result = await minutesService.getMembers();
        if (result.success && result.members) {
          setMembers(result.members);
          // Initialize attendance as "Not Present" for all members
          const initialAttendance: Record<string, string> = {};
          result.members.forEach((member: {name: string, address: string}) => {
            initialAttendance[member.name] = 'Not Present';
          });
          setAttendance(initialAttendance);
        }
      } catch (error) {
        console.error('Error loading members:', error);
        alert('Failed to load members. Please try again.');
      } finally {
        setIsLoadingMembers(false);
      }
    };

    if (user) {
      loadMembers();
    }
  }, [user]);

  const handlePreview = async () => {
    if (!meetingContent || !meetingContent.trim()) {
      alert('Please enter meeting content first');
      return;
    }

    setIsPreviewing(true);
    try {
      // Combine date and time for the API
      const dateTime = meetingDate && meetingTime ? `${meetingDate}T${meetingTime}` : (meetingDate || '');
      const result = await minutesService.previewMinutes(
        meetingContent,
        meetingTitle,
        dateTime,
        company,
        location
      );
      setPreviewData(result);
      setShowPreview(true);
    } catch (error: any) {
      console.error('Preview error:', error);
      const status = error.response?.status || error.status;
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      
      if (status === 429) {
        alert('⚠️ Gemini API Quota Exceeded\n\nYour free tier quota has been exhausted. Options:\n\n1. Wait a few minutes for the quota to reset\n2. Get a new Gemini API key from https://aistudio.google.com/\n3. Upgrade to a paid plan\n\nYou can still generate minutes without preview - it will use the content you provided.');
      } else {
        alert(`Error previewing content:\n\n${errorMessage}`);
      }
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleAttendanceChange = (memberName: string, status: string) => {
    setAttendance(prev => ({
      ...prev,
      [memberName]: status
    }));
  };

  const handleAllPresent = () => {
    const allPresent: Record<string, string> = {};
    members.forEach(member => {
      allPresent[member.name] = 'Present';
    });
    setAttendance(allPresent);
  };

  const handleSubmitAttendance = async () => {
    if (!meetingDate) {
      alert('Please select a date first');
      return;
    }

    if (members.length === 0) {
      alert('No members loaded. Please wait for members to load.');
      return;
    }

    console.log('Submitting attendance:', { date: meetingDate, attendance });
    
    setIsSubmittingAttendance(true);
    try {
      const result = await minutesService.submitAttendance(meetingDate, attendance);
      console.log('Attendance submission result:', result);
      
      if (result.success) {
        alert('Attendance submitted successfully!');
        
        // Update attendees and absent strings for display
        const presentNames = Object.entries(attendance)
          .filter(([_, status]) => status === 'Present')
          .map(([name, _]) => name);
        const absentNames = Object.entries(attendance)
          .filter(([_, status]) => status === 'Not Present')
          .map(([name, _]) => name);
        
        setAttendees(presentNames.join(', '));
        setAbsent(absentNames.join(', '));
      } else {
        alert('Failed to submit attendance. Please try again.');
      }
    } catch (error: any) {
      console.error('Error submitting attendance:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'Unknown error';
      alert(`Error submitting attendance:\n\n${errorMessage}\n\nPlease check the browser console for more details.`);
    } finally {
      setIsSubmittingAttendance(false);
    }
  };

  const handleGenerate = async () => {
    if (!meetingContent || !meetingContent.trim()) {
      alert('Please enter meeting content first');
      return;
    }

    setIsGenerating(true);
    try {
      // Combine date and time for the API
      const dateTime = meetingDate && meetingTime ? `${meetingDate}T${meetingTime}` : (meetingDate || '');
      const blob = await minutesService.generateMinutes(
        meetingContent,
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
    } catch (error: any) {
      console.error('Generation error:', error);
      const status = error.response?.status || error.status;
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      
      if (status === 429) {
        alert('⚠️ Gemini API Quota Exceeded\n\nYour free tier quota has been exhausted. The system will generate a basic meeting minutes document using the content you provided.\n\nOptions:\n1. Wait a few minutes for the quota to reset\n2. Get a new Gemini API key from https://aistudio.google.com/\n3. Upgrade to a paid plan\n\nNote: The document will still be generated, but without AI processing.');
      } else {
        alert(`Error generating meeting minutes:\n\n${errorMessage}`);
      }
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
            <h1 className="text-3xl font-bold text-black mb-2">Meeting Minutes</h1>
            <p className="text-black opacity-90">
              Enter meeting information and content to automatically generate standardized meeting minutes
            </p>
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
            </div>
          </div>

          {/* Attendance Section */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-white">Attendance</h2>
              <div className="flex gap-2">
                <button
                  onClick={handleAllPresent}
                  className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700"
                >
                  All Present
                </button>
                <button
                  onClick={handleSubmitAttendance}
                  disabled={isSubmittingAttendance || !meetingDate}
                  className="px-4 py-2 bg-cyan-600 text-white text-sm font-medium rounded-md hover:bg-cyan-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {isSubmittingAttendance ? 'Submitting...' : 'Submit Attendance'}
                </button>
              </div>
            </div>
            
            {isLoadingMembers ? (
              <div className="text-white text-center py-4">Loading members...</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                {members.map((member) => (
                  <div key={member.name} className="flex items-center space-x-3 bg-white p-3 rounded-md">
                    <input
                      type="checkbox"
                      checked={attendance[member.name] === 'Present'}
                      onChange={(e) => handleAttendanceChange(member.name, e.target.checked ? 'Present' : 'Not Present')}
                      className="w-5 h-5 text-cyan-600 border-gray-300 rounded focus:ring-cyan-500"
                    />
                    <label className="text-sm font-medium text-gray-700 flex-1 cursor-pointer">
                      {member.name}
                    </label>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Content Input Section */}
          <div className="rounded-lg shadow-sm border border-gray-200 p-6 mb-6" style={{ backgroundColor: '#6698CC' }}>
            <h2 className="text-xl font-semibold text-white mb-6">Meeting Content</h2>
            <div className="mb-6">
              <label className="block text-sm font-medium text-white mb-2">
                Enter meeting information, notes, or any content to be processed
              </label>
              <textarea
                value={meetingContent}
                onChange={(e) => setMeetingContent(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-cyan-500 focus:border-cyan-500 text-black bg-white placeholder-gray-500"
                placeholder="Paste meeting notes, agenda items, discussion points, or any relevant information here..."
                rows={8}
              />
              <p className="mt-2 text-sm text-white opacity-90">
                This content will be processed by AI to extract structured meeting information and generate formatted minutes.
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={handlePreview}
              disabled={!meetingContent || !meetingContent.trim() || isPreviewing}
              className="inline-flex items-center px-6 py-3 text-white text-sm font-medium rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ backgroundColor: '#F08C21' }}
            >
              <EyeIcon className="h-4 w-4 mr-2" />
              {isPreviewing ? 'Previewing...' : 'Preview Content'}
            </button>
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !meetingContent || !meetingContent.trim()}
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
