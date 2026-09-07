import React, { useState, useEffect } from 'react';
import TacticalSplashScreen from './components/TacticalSplashScreen';
import CommandCenterDashboard from './components/CommandCenterDashboard';
import AlertDispatchModal from './components/AlertDispatchModal';
import { Layers, Monitor, Bell, Play, X } from 'lucide-react';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // 'splash' | 'dashboard'
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [isDevSwitcherOpen, setIsDevSwitcherOpen] = useState(false);

  const sampleAlert = {
    id: 'EV-8842',
    title: 'TRIPWIRE BREACH DETECTED',
    sector: 'SECTOR 4A // NORTH POST',
    time: '06:24:12 UTC',
    severity: 'critical',
    target: 'Person (Armed) 94%',
    desc: 'Target crossed physical boundary tripwire vector #4. Heading South-East at 1.4m/s.',
    image: '/videos/cam_04_north_perimeter.mp4'
  };

  // Keyboard shortcut listener (` to toggle, Escape to close)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '`') {
        setIsDevSwitcherOpen(prev => !prev);
      } else if (e.key === 'Escape') {
        setIsDevSwitcherOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="relative w-full h-screen bg-[#0B1120] text-slate-100 overflow-hidden font-sans">
      
      {/* Collapsible Tactical Screen Switcher */}
      {!isDevSwitcherOpen ? (
        <button
          onClick={() => setIsDevSwitcherOpen(true)}
          title="Toggle Screen Switcher (Shortcut: `)"
          className="fixed bottom-2 right-2 z-50 px-2 py-1 bg-slate-900/70 hover:bg-slate-800 text-slate-400 hover:text-blue-300 text-[10px] font-mono rounded border border-slate-700/60 backdrop-blur-md transition flex items-center gap-1.5 shadow-lg opacity-60 hover:opacity-100"
        >
          <Layers className="w-3 h-3 text-blue-400" />
          <span>VIEWS</span>
        </button>
      ) : (
        <div className="fixed bottom-3 right-3 z-50 flex items-center gap-1.5 bg-slate-900/95 backdrop-blur-md border border-blue-500/60 p-1.5 rounded-lg shadow-[0_0_20px_rgba(0,0,0,0.8)] animate-fadeIn">
          <span className="text-[10px] font-mono font-bold text-slate-400 px-2 flex items-center gap-1 border-r border-slate-700">
            <Layers className="w-3 h-3 text-blue-400" />
            VIEWS:
          </span>
          <button
            onClick={() => {
              setCurrentView('splash');
              setSelectedAlert(null);
            }}
            className={`px-2 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
              currentView === 'splash'
                ? 'bg-blue-600 text-white font-bold shadow-[0_0_10px_rgba(59,130,246,0.5)]'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Play className="w-3 h-3" />
            1. Splash
          </button>
          <button
            onClick={() => {
              setCurrentView('dashboard');
              setSelectedAlert(null);
            }}
            className={`px-2 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
              currentView === 'dashboard' && !selectedAlert
                ? 'bg-blue-600 text-white font-bold shadow-[0_0_10px_rgba(59,130,246,0.5)]'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Monitor className="w-3 h-3" />
            2. Dashboard
          </button>
          <button
            onClick={() => {
              setCurrentView('dashboard');
              setSelectedAlert(sampleAlert);
            }}
            className={`px-2 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
              selectedAlert
                ? 'bg-red-600 text-white font-bold shadow-[0_0_10px_rgba(239,68,68,0.5)]'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Bell className="w-3 h-3" />
            3. Dispatch Modal
          </button>
          <button
            onClick={() => setIsDevSwitcherOpen(false)}
            title="Collapse (Esc)"
            className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition ml-1"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main View Area */}
      {currentView === 'splash' ? (
        <TacticalSplashScreen onComplete={() => setCurrentView('dashboard')} />
      ) : (
        <CommandCenterDashboard onSelectAlert={(alert) => setSelectedAlert(alert)} />
      )}

      {/* Alert Details & QRT Dispatch Modal (Screen 3) */}
      {selectedAlert && (
        <AlertDispatchModal
          alert={selectedAlert}
          onClose={() => setSelectedAlert(null)}
          onDispatch={(unit) => {
            console.log(`QRT Unit ${unit} dispatched!`);
          }}
        />
      )}

    </div>
  );
}
