import React, { useState } from 'react';
import TacticalSplashScreen from './components/TacticalSplashScreen';
import CommandCenterDashboard from './components/CommandCenterDashboard';
import AlertDispatchModal from './components/AlertDispatchModal';
import { Layers, Monitor, Bell, Play } from 'lucide-react';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // 'splash' | 'dashboard'
  const [selectedAlert, setSelectedAlert] = useState(null);

  const sampleAlert = {
    id: 'EV-8842',
    title: 'TRIPWIRE BREACH DETECTED',
    sector: 'SECTOR 4A // NORTH POST',
    time: '06:24:12 UTC',
    severity: 'critical',
    target: 'Person (Armed) 94%',
    desc: 'Target crossed physical boundary tripwire vector #4. Heading South-East at 1.4m/s.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM'
  };

  return (
    <div className="relative w-full h-screen bg-[#0B1120] text-slate-100 overflow-hidden font-sans">
      
      {/* Floating Tactical Screen Switcher for Testing & Review */}
      <div className="fixed bottom-3 right-4 z-50 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md border border-slate-700/80 p-1.5 rounded-lg shadow-2xl">
        <span className="text-[10px] font-mono font-bold text-slate-400 px-2 flex items-center gap-1 border-r border-slate-700">
          <Layers className="w-3 h-3 text-blue-400" />
          STITCH SCREENS:
        </span>
        <button
          onClick={() => {
            setCurrentView('splash');
            setSelectedAlert(null);
          }}
          className={`px-2.5 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
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
          className={`px-2.5 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
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
          className={`px-2.5 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition ${
            selectedAlert
              ? 'bg-red-600 text-white font-bold shadow-[0_0_10px_rgba(239,68,68,0.5)]'
              : 'text-slate-400 hover:text-white hover:bg-slate-800'
          }`}
        >
          <Bell className="w-3 h-3" />
          3. Dispatch Modal
        </button>
      </div>

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
