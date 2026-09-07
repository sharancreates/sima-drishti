import React, { useState, useEffect } from 'react';
import { 
  Shield, ShieldCheck, Video, Cpu, Clock, Calendar, Volume2, 
  AlertTriangle, SignalHigh, Wifi, Zap, UserX, Truck, Crosshair, 
  Camera, Maximize2, ZoomIn, ZoomOut, Flame, Moon, Sun, 
  MapPin, Radio, Activity, ChevronRight, Layers, BellRing, RefreshCw
} from 'lucide-react';

const mockCameras = [
  { id: 'cam-01', name: 'CAM-01 · GATE ALPHA', status: 'ONLINE', fps: 30, sector: 'SEC-1' },
  { id: 'cam-02', name: 'CAM-02 · FENCE BRAVO', status: 'ONLINE', fps: 30, sector: 'SEC-2' },
  { id: 'cam-03', name: 'CAM-03 · RIVERINE WATCH', status: 'ONLINE', fps: 28, sector: 'SEC-3' },
  { id: 'cam-04', name: 'CAM-04 · NORTH PERIMETER', status: 'ALERT', fps: 30, sector: 'SEC-4A' }
];

const mockAlerts = [
  {
    id: 'EV-8842',
    title: 'TRIPWIRE BREACH DETECTED',
    sector: 'SECTOR 4A // NORTH POST',
    time: '06:24:12 UTC',
    severity: 'critical',
    target: 'Person (Armed) 94%',
    desc: 'Target crossed physical boundary tripwire vector #4. Heading South-East at 1.4m/s.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM'
  },
  {
    id: 'EV-8839',
    title: 'VEHICLE PROXIMITY LOITERING',
    sector: 'SECTOR 2B // SERVICE ROAD',
    time: '06:19:40 UTC',
    severity: 'warning',
    target: 'Vehicle 87%',
    desc: 'Stationary pickup truck in restricted buffer zone exceeding 3 minutes dwell time.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM'
  },
  {
    id: 'EV-8821',
    title: 'THERMAL FLIR HEAT SIGNATURE',
    sector: 'SECTOR 1C // DENSE BRUSH',
    time: '05:58:11 UTC',
    severity: 'caution',
    target: 'Biological Cluster',
    desc: 'Infrared FLIR detection: clustered heat signatures 120m from international border.',
    image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM'
  }
];

const BACKEND_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws/alerts";

function normalizeBackendAlert(data) {
  const isPerson = (data.object_class || '').toLowerCase() === 'person';
  const displayClass = data.object_class
    ? (data.object_class.charAt(0).toUpperCase() + data.object_class.slice(1))
    : 'Target';
  const confidencePct = data.confidence ? `${Math.round(data.confidence * 100)}%` : '94%';
  const timeStr = data.timestamp 
    ? (new Date(data.timestamp).toISOString().substring(11, 19) + ' UTC')
    : (new Date().toISOString().substring(11, 19) + ' UTC');

  const fullImageUrl = data.thumbnail 
    ? (data.thumbnail.startsWith('http') ? data.thumbnail : `${BACKEND_URL}${data.thumbnail}`)
    : (data.image || 'https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM');

  return {
    id: data.alert_id ? `EV-${data.alert_id}` : (data.id || `EV-${Math.floor(Math.random() * 9000 + 1000)}`),
    alert_id: data.alert_id || data.id,
    title: data.title || (isPerson ? 'TRIPWIRE BREACH DETECTED' : `${displayClass.toUpperCase()} PERIMETER ALERT`),
    sector: data.zone ? `${data.zone.toUpperCase()} // SECTOR` : (data.sector || 'SECTOR 04-NORTH'),
    zone: data.zone || data.sector || 'Sector_Alpha',
    time: timeStr,
    timestamp: data.timestamp || new Date().toISOString(),
    severity: data.severity || (isPerson ? 'critical' : 'warning'),
    target: data.target || `${displayClass} ${confidencePct}`,
    object_class: data.object_class || 'person',
    confidence: data.confidence || 0.94,
    desc: data.desc || `Target ${displayClass.toLowerCase()} crossed tactical perimeter vector. Coordinates: ${data.lat || 31.4392}° N / ${data.lng || 74.3298}° E.`,
    image: fullImageUrl,
    thumbnail: data.thumbnail || fullImageUrl,
    lat: data.lat || 31.4392,
    lng: data.lng || 74.3298,
    isLive: data.isLive ?? false
  };
}

export default function CommandCenterDashboard({ onSelectAlert }) {
  const [activeCam, setActiveCam] = useState('cam-04');
  const [viewMode, setViewMode] = useState('optical'); // optical, thermal, night
  const [zoomLevel, setZoomLevel] = useState(1);
  const [clock, setClock] = useState('06:24:18 UTC');
  const [date, setDate] = useState('2026-03-29');

  // Real-time dynamic state
  const [alerts, setAlerts] = useState(mockAlerts);
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // 'connected' | 'connecting' | 'offline'
  const [backendStats, setBackendStats] = useState({
    total_alerts: 0,
    alerts_last_24h: 0,
    active_zones: 4,
    hardware_status: 'standby'
  });
  const [alarmActive, setAlarmActive] = useState(false);

  // Tactical sound synthesizer
  const playTacticalBeep = (freq = 880, duration = 0.25) => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(freq / 2, ctx.currentTime + duration);
      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + duration);
    } catch {
      // Audio autoplay policy fallback
    }
  };

  const toggleAlarm = () => {
    setAlarmActive(prev => !prev);
    playTacticalBeep(920, 0.4);
  };

  // Clock interval
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setClock(now.toISOString().substring(11, 19) + ' UTC');
      setDate(now.toISOString().substring(0, 10));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // REST Synchronization & WebSocket Real-time Ingestion
  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;
    let isMounted = true;

    const fetchInitialData = async () => {
      try {
        const [alertsRes, analyticsRes] = await Promise.allSettled([
          fetch(`${BACKEND_URL}/alerts?limit=25`),
          fetch(`${BACKEND_URL}/analytics`)
        ]);

        if (!isMounted) return;

        if (analyticsRes.status === 'fulfilled' && analyticsRes.value.ok) {
          const stats = await analyticsRes.value.json();
          setBackendStats(stats);
        }

        if (alertsRes.status === 'fulfilled' && alertsRes.value.ok) {
          const dbAlerts = await alertsRes.value.json();
          if (Array.isArray(dbAlerts) && dbAlerts.length > 0) {
            const normalized = dbAlerts.map(normalizeBackendAlert);
            setAlerts(prev => {
              const ids = new Set(normalized.map(a => a.id));
              const nonDuplicateDefaults = prev.filter(a => !ids.has(a.id));
              return [...normalized, ...nonDuplicateDefaults];
            });
          }
        }
      } catch (err) {
        console.warn('[NOC Telemetry] Backend REST service offline, operating in simulation mode:', err);
      }
    };

    fetchInitialData();

    const connectWebSocket = () => {
      if (!isMounted) return;
      setConnectionStatus('connecting');

      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          if (!isMounted) return;
          console.log('[NOC WebSocket] Connected to tactical stream:', WS_URL);
          setConnectionStatus('connected');
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const payload = JSON.parse(event.data);
            console.log('[NOC WebSocket] Breach event broadcast received:', payload);
            const liveAlert = normalizeBackendAlert({ ...payload, isLive: true });
            
            // Trigger tactical audio chime on intrusion
            playTacticalBeep(980, 0.35);

            setAlerts(prev => [liveAlert, ...prev.slice(0, 49)]);
            setBackendStats(prev => ({
              ...prev,
              total_alerts: (prev.total_alerts || 0) + 1,
              alerts_last_24h: (prev.alerts_last_24h || 0) + 1
            }));
          } catch (e) {
            console.error('[NOC WebSocket] Failed parsing alert broadcast:', e);
          }
        };

        ws.onclose = () => {
          if (!isMounted) return;
          console.warn('[NOC WebSocket] Disconnected from server. Reconnecting in 3.5s...');
          setConnectionStatus('offline');
          reconnectTimeout = setTimeout(connectWebSocket, 3500);
        };

        ws.onerror = (err) => {
          if (!isMounted) return;
          console.warn('[NOC WebSocket] Connection error:', err);
          setConnectionStatus('offline');
          try { ws.close(); } catch {}
        };
      } catch (e) {
        if (!isMounted) return;
        setConnectionStatus('offline');
        reconnectTimeout = setTimeout(connectWebSocket, 3500);
      }
    };

    connectWebSocket();

    return () => {
      isMounted = false;
      if (ws) {
        ws.onclose = null; // Prevent reconnect loop
        try { ws.close(); } catch {}
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0F172A] text-slate-100 font-sans overflow-hidden select-none">
      
      {/* TOP BAR: Persistent Command Header */}
      <header className="h-14 bg-[#131E35] border-b border-slate-700/80 px-4 flex items-center justify-between shrink-0 z-30 shadow-md">
        
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-[0_0_12px_rgba(59,130,246,0.3)]">
            <ShieldCheck className="w-5 h-5 text-blue-400" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-wider text-white uppercase font-sans">
                Border<span className="text-blue-400 font-light">Vision</span>
              </span>
              <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/30">
                NOC v2.4
              </span>
            </div>
            <span className="text-[10px] font-mono tracking-widest text-slate-400 uppercase">
              AI Tactical Perimeter Defense
            </span>
          </div>

          <div className="h-5 w-[1px] bg-slate-700 mx-2 hidden md:block"></div>

          {/* Telemetry Chips */}
          <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700">
              <Video className="w-3.5 h-3.5 text-blue-400" />
              Active Feeds: <span className="text-slate-200 font-semibold">12/12</span>
            </span>
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              Inference: <span className="text-slate-200 font-semibold">18.4ms</span>
            </span>
          </div>
        </div>

        {/* Center: Clock & Date */}
        <div className="flex items-center gap-4 bg-slate-900/90 border border-slate-700/80 px-3.5 py-1 rounded-md shadow-inner">
          <div className="flex items-center gap-2 text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-bold tracking-widest text-slate-100 text-sm">{clock}</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 hidden sm:flex">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>{date}</span>
          </div>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-[11px] font-mono text-blue-400 uppercase tracking-wider font-semibold">
            SEC-NORTH-4
          </span>
        </div>

        {/* Right: Operational Status Pill & Controls */}
        <div className="flex items-center gap-3">
          {connectionStatus === 'connected' ? (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono shadow-[0_0_10px_rgba(16,185,129,0.2)]">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span className="font-semibold tracking-wide">SYSTEM ONLINE // WS LIVE</span>
            </div>
          ) : connectionStatus === 'connecting' ? (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span className="font-semibold tracking-wide">CONNECTING TO NOC...</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-red-400"></span>
              <span className="font-semibold tracking-wide">OFFLINE // SIMULATION MODE</span>
            </div>
          )}

          <div className="flex items-center gap-1">
            <button
              onClick={toggleAlarm}
              title={alarmActive ? "Siren Alarm Triggered (Click to Mute)" : "Sound Tactical Perimeter Siren"}
              className={`h-8 w-8 rounded border flex items-center justify-center transition ${
                alarmActive
                  ? 'bg-red-600 text-white border-red-400 shadow-[0_0_12px_rgba(239,68,68,0.6)] animate-pulse'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300'
              }`}
            >
              <Volume2 className="w-4 h-4" />
            </button>
            <button
              title="Threat Advisory Level 2"
              className="h-8 px-2.5 rounded bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/40 flex items-center gap-1.5 text-amber-300 text-xs font-mono transition"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span className="font-bold">DEFCON 3</span>
            </button>
          </div>
        </div>
      </header>

      {/* MAIN OPERATOR VIEW: Grid layout */}
      <main className="flex-1 p-3 gap-3 overflow-hidden grid grid-cols-12 max-h-[calc(100vh-3.5rem)]">
        
        {/* LEFT COLUMN: PRIMARY CAMERA FEED */}
        <section className="col-span-12 lg:col-span-7 xl:col-span-8 flex flex-col bg-[#131E35] border border-slate-700/80 rounded-lg overflow-hidden shadow-xl">
          
          {/* Camera Sub-header */}
          <div className="h-10 bg-slate-900/90 border-b border-slate-700/80 px-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse"></span>
              <span className="font-bold text-slate-100 tracking-wide">PRIMARY SURVEILLANCE FEED</span>
              <span className="text-slate-500">//</span>
              <span className="text-blue-400 font-semibold">CAM-04 [SECTOR 4A · NORTH PERIMETER]</span>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="text-slate-400 hidden sm:inline">RTSP://192.168.4.108:554/live</span>
              <div className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                <Wifi className="w-3 h-3" />
                <span>30 FPS · 4K</span>
              </div>
            </div>
          </div>

          {/* Live Video Viewport */}
          <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center group">
            {/* Camera feed image */}
            <img 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCumfyk0VITQQhCi4VRbB6Ra_80yobpm3tx3tRvbC5If2U4QFwJXR2LNXSPycdk9z8QdkUGw0DjIoVypH4kusiVPBqS8dCzJU0VRvNgFUZ8uitNB-A5SXs89tdvg4H6dbTED0v8MHKzRiucen7u8uZhhLvhLykP3dauxH3kK2gy5wS0pOip7XaKooLhHhE0FKAx5R0WfP5MQArkHR-ER4aVNSl2bubJSmeHaKUoGdkbm85tRkrsLzM" 
              alt="Live Surveillance" 
              className={`w-full h-full object-cover transition duration-300 ${
                viewMode === 'thermal'
                  ? 'filter hue-rotate-180 invert contrast-150'
                  : viewMode === 'night'
                  ? 'filter sepia hue-rotate-90 brightness-110 contrast-125'
                  : 'opacity-90 filter contrast-125 brightness-95'
              }`}
              style={{ transform: `scale(${zoomLevel})` }}
            />

            {/* Overlays: Scanlines & Vignette */}
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_55%,rgba(0,0,0,0.75)_100%)]"></div>
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.35)_50%)] bg-[length:100%_4px] opacity-40"></div>

            {/* Top Badges */}
            <div className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded border border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.4)]">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
              </span>
              <span className="text-xs font-mono font-bold tracking-widest text-red-100">LIVE FEED</span>
              <span className="text-[10px] font-mono text-slate-400 px-1 bg-slate-800 rounded">0.08s LATENCY</span>
            </div>

            <div className="absolute top-4 right-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded border border-emerald-500/40 shadow-sm">
              <SignalHigh className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span className="text-xs font-mono font-bold tracking-wider text-emerald-400">CAMERA ONLINE</span>
              <span className="text-[10px] font-mono text-slate-400 border-l border-slate-700 pl-2">99.8% SIGNAL</span>
            </div>

            {/* Corner brackets */}
            <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-blue-400 pointer-events-none"></div>
            <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-blue-400 pointer-events-none"></div>
            <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-blue-400 pointer-events-none"></div>
            <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-blue-400 pointer-events-none"></div>

            {/* VIRTUAL TRIPWIRE LINE */}
            <div className="absolute left-0 right-0 top-[62%] h-[2px] tripwire-line pointer-events-none z-10">
              <div className="absolute right-6 -top-5 flex items-center gap-1.5 bg-red-950/90 text-red-300 border border-red-500/60 px-2 py-0.5 rounded text-[10px] font-mono tracking-widest uppercase">
                <Zap className="w-3 h-3 text-red-400 fill-red-400" />
                <span>VIRTUAL TRIPWIRE [PERIMETER 04] // ACTIVE</span>
              </div>
              <div className="w-full flex justify-between px-10 text-[9px] font-mono text-red-400/80 -mt-3.5">
                <span>| 00m</span>
                <span>| 25m</span>
                <span className="text-red-300 font-bold">| 50m (BREACHED)</span>
                <span>| 75m</span>
                <span>| 100m</span>
              </div>
            </div>

            {/* BOUNDING BOX: DETECTED PERSON */}
            <div
              onClick={() => onSelectAlert(mockAlerts[0])}
              className="absolute right-[22%] top-[51%] w-[95px] h-[190px] border-2 border-red-500 bbox-person bg-red-500/10 cursor-pointer z-20 hover:scale-105 transition"
            >
              <div className="absolute -top-7 left-[-2px] bg-red-600 text-white font-mono font-bold text-[10px] px-2 py-0.5 flex items-center gap-1.5 shadow-md uppercase tracking-wider whitespace-nowrap">
                <UserX className="w-3 h-3" />
                <span>Person 94%</span>
                <span className="text-[8px] bg-red-800 px-1 rounded">BREACH</span>
              </div>
              <div className="absolute -bottom-5 left-0 text-[10px] font-mono bg-black/80 text-red-300 px-1.5 py-0.2 rounded border border-red-500/40">
                ID: #T-8092 · 1.4 m/s
              </div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-red-400/70">
                <Crosshair className="w-4 h-4 animate-spin" />
              </div>
            </div>

            {/* BOUNDING BOX: DETECTED VEHICLE */}
            <div className="absolute right-[33%] top-[45%] w-[85px] h-[55px] border-2 border-blue-400 bbox-vehicle bg-blue-500/10 pointer-events-none z-20">
              <div className="absolute -top-6 left-[-2px] bg-blue-600 text-white font-mono font-bold text-[10px] px-1.5 py-0.5 flex items-center gap-1 shadow uppercase whitespace-nowrap">
                <Truck className="w-3 h-3" />
                <span>Vehicle 87%</span>
              </div>
              <div className="absolute -bottom-5 left-0 text-[9px] font-mono bg-black/80 text-blue-300 px-1 py-0.2 rounded border border-blue-500/40">
                ID: #V-104 · STATIONARY
              </div>
            </div>

          </div>

          {/* Bottom Feed Control Bar */}
          <div className="h-12 bg-slate-900/95 border-t border-slate-700/80 px-3 flex items-center justify-between shrink-0">
            {/* Mode toggles */}
            <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-md border border-slate-700 text-xs font-mono">
              <button
                onClick={() => setViewMode('optical')}
                className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition ${
                  viewMode === 'optical' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sun className="w-3.5 h-3.5" />
                <span>OPTICAL</span>
              </button>
              <button
                onClick={() => setViewMode('thermal')}
                className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition ${
                  viewMode === 'thermal' ? 'bg-amber-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Flame className="w-3.5 h-3.5" />
                <span>FLIR THERMAL</span>
              </button>
              <button
                onClick={() => setViewMode('night')}
                className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition ${
                  viewMode === 'night' ? 'bg-emerald-600 text-white font-bold' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Moon className="w-3.5 h-3.5" />
                <span>NIGHT IR</span>
              </button>
            </div>

            {/* PTZ Zoom & Tools */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-slate-800 px-2 py-1 rounded border border-slate-700 text-xs font-mono">
                <button
                  onClick={() => setZoomLevel(prev => Math.max(1, prev - 0.25))}
                  className="p-1 hover:text-blue-400"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-slate-300 w-12 text-center">{zoomLevel.toFixed(1)}x</span>
                <button
                  onClick={() => setZoomLevel(prev => Math.min(3, prev + 0.25))}
                  className="p-1 hover:text-blue-400"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
              </div>

              <button
                onClick={() => onSelectAlert(mockAlerts[0])}
                className="px-3 py-1 bg-red-600/90 hover:bg-red-500 text-white text-xs font-mono font-bold rounded border border-red-500/50 flex items-center gap-1.5 shadow-[0_0_10px_rgba(239,68,68,0.4)] transition"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                DISPATCH MODAL
              </button>
            </div>
          </div>

          {/* Mini-camera Selector Grid */}
          <div className="h-16 bg-[#0B1120] border-t border-slate-800 px-3 py-2 grid grid-cols-4 gap-2 shrink-0">
            {mockCameras.map(cam => (
              <button
                key={cam.id}
                onClick={() => setActiveCam(cam.id)}
                className={`flex items-center justify-between px-2.5 py-1.5 rounded border text-left font-mono transition ${
                  activeCam === cam.id
                    ? 'bg-blue-950/70 border-blue-500 text-blue-300 shadow-[0_0_10px_rgba(59,130,246,0.3)]'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="truncate">
                  <div className="text-[11px] font-bold text-white truncate">{cam.name}</div>
                  <div className="text-[9px] text-slate-500">{cam.sector}</div>
                </div>
                <span className={`text-[9px] font-bold px-1 rounded ${
                  cam.status === 'ALERT' ? 'bg-red-950 text-red-400 animate-pulse' : 'bg-emerald-950 text-emerald-400'
                }`}>
                  {cam.status}
                </span>
              </button>
            ))}
          </div>

        </section>

        {/* RIGHT COLUMN: REAL-TIME THREAT & INCIDENT FEED */}
        <section className="col-span-12 lg:col-span-5 xl:col-span-4 flex flex-col bg-[#131E35] border border-slate-700/80 rounded-lg overflow-hidden shadow-xl">
          
          {/* Header */}
          <div className="h-10 bg-slate-900/90 border-b border-slate-700/80 px-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200">
              <BellRing className="w-4 h-4 text-red-400 animate-bounce" />
              <span>LIVE INCIDENT & THREAT FEED</span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                <span className="text-red-400 font-bold">{alerts.length} ACTIVE</span>
              </span>
              {connectionStatus === 'connected' && (
                <span className="px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-600 text-[9px] font-bold">
                  WS LIVE
                </span>
              )}
            </div>
          </div>

          {/* Alerts List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {alerts.map(alert => (
              <div
                key={alert.id}
                onClick={() => onSelectAlert(alert)}
                className={`p-3 rounded-lg border transition cursor-pointer flex flex-col gap-2 ${
                  alert.severity === 'critical'
                    ? 'bg-red-950/40 border-red-500/70 hover:border-red-400 shadow-[0_0_15px_rgba(239,68,68,0.2)]'
                    : alert.severity === 'warning'
                    ? 'bg-amber-950/30 border-amber-500/50 hover:border-amber-400'
                    : 'bg-slate-900/60 border-slate-700/70 hover:border-slate-600'
                }`}
              >
                {/* Alert Top */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      alert.severity === 'critical' ? 'bg-red-500 animate-ping' : 'bg-amber-400'
                    }`}></span>
                    <span className="font-mono text-xs font-bold text-white tracking-wider">
                      {alert.title}
                    </span>
                    {alert.isLive && (
                      <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-red-600 text-white font-bold tracking-wider animate-pulse">
                        LIVE BREACH
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">{alert.time}</span>
                </div>

                {/* Details */}
                <div className="text-[11px] font-mono text-slate-300">
                  <span className="text-slate-400">Target:</span>{' '}
                  <span className="font-bold text-white">{alert.target}</span>
                </div>

                <p className="text-xs text-slate-400 leading-snug">
                  {alert.desc}
                </p>

                {/* Footer buttons */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 mt-1">
                  <span className="text-[10px] font-mono text-blue-400 font-semibold">
                    {alert.sector}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectAlert(alert);
                    }}
                    className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white font-mono text-[10px] font-bold rounded flex items-center gap-1 transition"
                  >
                    <span>INSPECT & DISPATCH</span>
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}

            {/* Tactical Sector Map Mini-card */}
            <div className="p-3 bg-[#0B1120] border border-slate-800 rounded-lg space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold border-b border-slate-800 pb-1.5">
                <span className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-400" />
                  SECTOR GPS COORDINATES
                </span>
                <span className="text-emerald-400 text-[10px]">RADAR LOCK</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-400">
                <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">POST LAT/LONG:</span>
                  <span className="text-white font-bold">31.4392° N / 74.3298° E</span>
                </div>
                <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">RADAR RANGE:</span>
                  <span className="text-blue-400 font-bold">2.5 KM RADIUS</span>
                </div>
              </div>
            </div>

          </div>

        </section>

      </main>
    </div>
  );
}
