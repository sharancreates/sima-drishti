import React, { useState, useEffect, useRef } from 'react';
import { 
  Shield, ShieldCheck, Video, Cpu, Clock, Calendar, Volume2, 
  AlertTriangle, SignalHigh, Wifi, Zap, UserX, Truck, Crosshair, 
  Camera, Maximize2, ZoomIn, ZoomOut, Flame, Moon, Sun, 
  MapPin, Radio, Activity, ChevronRight, Layers, BellRing, 
  RefreshCw, Eye, Target, Compass, Thermometer
} from 'lucide-react';

const mockCameras = [
  {
    id: 'cam-01',
    name: 'CAM-01 · GATE ALPHA',
    status: 'ONLINE',
    fps: 30,
    sector: 'SEC-1',
    sectorName: 'SECTOR 1A · GATEWAY ALPHA',
    rtspUrl: 'rtsp://192.168.1.101:554/ch01/main',
    resolution: '1080P · 30 FPS',
    videoSrc: '/videos/cam_02_fence_bravo.mp4',
    telemetry: { lat: 31.4385, lng: 74.3210, az: '042° NE', fov: '85°' },
    tripwirePolygon: '20,45 80,45 88,88 12,88',
    tripwirePoints: [[0.20, 0.45], [0.80, 0.45], [0.88, 0.88], [0.12, 0.88]],
    isAlert: false,
    detections: []
  },
  {
    id: 'cam-02',
    name: 'CAM-02 · FENCE BRAVO',
    status: 'ONLINE',
    fps: 30,
    sector: 'SEC-2',
    sectorName: 'SECTOR 2B · FENCE PERIMETER BRAVO',
    rtspUrl: 'rtsp://192.168.2.102:554/ch01/main',
    resolution: '2K · 30 FPS',
    videoSrc: '/videos/cam_02_fence_bravo.mp4',
    telemetry: { lat: 31.4398, lng: 74.3245, az: '118° ESE', fov: '92°' },
    tripwirePolygon: '10,48 90,48 95,92 5,92',
    tripwirePoints: [[0.10, 0.48], [0.90, 0.48], [0.95, 0.92], [0.05, 0.92]],
    isAlert: false,
    detections: [
      {
        id: 'TRK-201',
        class: 'vehicle',
        label: 'Vehicle 87%',
        confidence: 0.87,
        bbox: { left: '16%', top: '44%', width: '135px', height: '85px' },
        badge: 'LOITERING',
        badgeColor: 'amber',
        telemetry: 'ID: #V-104 · STATIONARY',
        speed: '0.0 km/h',
        isBreached: false
      }
    ]
  },
  {
    id: 'cam-03',
    name: 'CAM-03 · RIVERINE WATCH',
    status: 'ONLINE',
    fps: 28,
    sector: 'SEC-3',
    sectorName: 'SECTOR 3C · RIVERINE EMBANKMENT',
    rtspUrl: 'rtsp://192.168.3.103:554/ch01/main',
    resolution: '1080P · 28 FPS',
    videoSrc: '/videos/cam_04_north_perimeter.mp4',
    telemetry: { lat: 31.4421, lng: 74.3270, az: '280° WNW', fov: '110°' },
    tripwirePolygon: '15,35 85,35 92,85 8,85',
    tripwirePoints: [[0.15, 0.35], [0.85, 0.35], [0.92, 0.85], [0.08, 0.85]],
    isAlert: false,
    detections: []
  },
  {
    id: 'cam-04',
    name: 'CAM-04 · NORTH PERIMETER',
    status: 'ALERT',
    fps: 30,
    sector: 'SEC-4A',
    sectorName: 'SECTOR 4A · NORTH PERIMETER',
    rtspUrl: 'rtsp://192.168.4.108:554/live',
    resolution: '4K · 30 FPS',
    videoSrc: '/videos/cam_04_north_perimeter.mp4',
    telemetry: { lat: 31.4392, lng: 74.3298, az: '015° NNE', fov: '120°' },
    // Matches ZONE_COORDINATE_RATIOS = [(0.15, 0.40), (0.85, 0.40), (0.95, 0.90), (0.05, 0.90)]
    tripwirePolygon: '15,40 85,40 95,90 5,90',
    tripwirePoints: [[0.15, 0.40], [0.85, 0.40], [0.95, 0.90], [0.05, 0.90]],
    isAlert: true,
    detections: [
      {
        id: 'TRK-8092',
        class: 'person',
        label: 'Person 94%',
        confidence: 0.94,
        bbox: { right: '22%', top: '46%', width: '105px', height: '190px' },
        badge: 'BREACH',
        badgeColor: 'red',
        telemetry: 'ID: #T-8092 · 1.4 m/s',
        speed: '1.4 m/s',
        isBreached: true
      },
      {
        id: 'TRK-104',
        class: 'vehicle',
        label: 'Vehicle 87%',
        confidence: 0.87,
        bbox: { right: '35%', top: '44%', width: '90px', height: '60px' },
        badge: 'BUFFER ZONE',
        badgeColor: 'blue',
        telemetry: 'ID: #V-104 · STATIONARY',
        speed: '0.0 km/h',
        isBreached: false
      }
    ]
  }
];

const mockAlerts = [
  {
    id: 'EV-8842',
    title: 'TRIPWIRE BREACH DETECTED',
    sector: 'SECTOR 4A // NORTH POST',
    zone: 'Sector_North_4A',
    time: '06:24:12 UTC',
    severity: 'critical',
    target: 'Person (Armed) 94%',
    object_class: 'person',
    confidence: 0.94,
    lat: 31.4392,
    lng: 74.3298,
    desc: 'Target crossed physical boundary tripwire vector #4. Heading South-East at 1.4m/s.',
    image: '/videos/cam_04_north_perimeter.mp4'
  },
  {
    id: 'EV-8839',
    title: 'VEHICLE PROXIMITY LOITERING',
    sector: 'SECTOR 2B // SERVICE ROAD',
    zone: 'Sector_Fence_Bravo',
    time: '06:19:40 UTC',
    severity: 'warning',
    target: 'Vehicle 87%',
    object_class: 'vehicle',
    confidence: 0.87,
    lat: 31.4398,
    lng: 74.3245,
    desc: 'Stationary pickup truck in restricted buffer zone exceeding 3 minutes dwell time.',
    image: '/videos/cam_02_fence_bravo.mp4'
  },
  {
    id: 'EV-8821',
    title: 'THERMAL FLIR HEAT SIGNATURE',
    sector: 'SECTOR 1C // DENSE BRUSH',
    zone: 'Sector_Brush_1C',
    time: '05:58:11 UTC',
    severity: 'caution',
    target: 'Biological Cluster',
    object_class: 'person',
    confidence: 0.78,
    lat: 31.4385,
    lng: 74.3210,
    desc: 'Infrared FLIR detection: clustered heat signatures 120m from international border.',
    image: '/videos/cam_04_north_perimeter.mp4'
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
    : (data.image || '/videos/cam_04_north_perimeter.mp4');

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
  const videoRef = useRef(null);

  // Active camera model
  const currentCam = mockCameras.find(c => c.id === activeCam) || mockCameras[3];

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

  // Handle camera switch
  const handleSelectCamera = (camId) => {
    setActiveCam(camId);
    playTacticalBeep(720, 0.15);
  };

  // Handle sensor mode switch
  const handleSelectMode = (mode) => {
    setViewMode(mode);
    playTacticalBeep(840, 0.12);
  };

  // Trigger dispatch from detection click
  const handleDetectionClick = (detection) => {
    playTacticalBeep(1020, 0.25);
    const associatedAlert = alerts.find(a => a.severity === 'critical') || alerts[0];
    onSelectAlert({
      ...associatedAlert,
      id: `EV-${detection.id}`,
      title: detection.isBreached ? 'TRIPWIRE BREACH DETECTED' : `${detection.class.toUpperCase()} PROXIMITY ALERT`,
      target: detection.label,
      sector: currentCam.sectorName,
      zone: currentCam.sector,
      time: clock,
      desc: `Target ${detection.label} intercepted by automated tracking in ${currentCam.sectorName}. Velocity: ${detection.speed}. Coordinates: ${currentCam.telemetry.lat}° N / ${currentCam.telemetry.lng}° E.`
    });
  };

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
              Active Feeds: <span className="text-slate-200 font-semibold">4/4</span>
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
            {currentCam.sector}
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
              <span className={`h-2 w-2 rounded-full ${currentCam.status === 'ALERT' ? 'bg-red-500 animate-pulse' : 'bg-emerald-400'}`}></span>
              <span className="font-bold text-slate-100 tracking-wide">PRIMARY SURVEILLANCE FEED</span>
              <span className="text-slate-500">//</span>
              <span className={currentCam.status === 'ALERT' ? "text-red-400 font-semibold" : "text-blue-400 font-semibold"}>
                {currentCam.name} [{currentCam.sector}]
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="text-slate-400 hidden sm:inline">{currentCam.rtspUrl}</span>
              <div className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                <Wifi className="w-3 h-3" />
                <span>{currentCam.resolution}</span>
              </div>
            </div>
          </div>

          {/* Live Video Viewport */}
          <div className="relative flex-1 bg-black overflow-hidden flex items-center justify-center group">
            
            {/* Real HTML5 Surveillance Video Element */}
            <video 
              ref={videoRef}
              key={currentCam.id}
              src={currentCam.videoSrc}
              autoPlay
              loop
              muted
              playsInline
              className={`w-full h-full object-cover transition-all duration-300 ${
                viewMode === 'thermal'
                  ? 'filter invert contrast-[180%] brightness-110 hue-rotate-180 saturate-[220%]'
                  : viewMode === 'night'
                  ? 'filter sepia-[100%] hue-rotate-[85deg] brightness-125 contrast-[150%] saturate-[200%]'
                  : 'opacity-95 filter contrast-125 brightness-95'
              }`}
              style={{ 
                transform: `scale(${zoomLevel})`,
                transformOrigin: 'center center'
              }}
            />

            {/* Overlays: Tactical Scanlines & Vignette */}
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_50%,rgba(0,0,0,0.85)_100%)]"></div>
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.35)_50%)] bg-[length:100%_4px] opacity-35"></div>

            {/* View Mode Specific HUD Elements */}
            {viewMode === 'thermal' && (
              <>
                {/* FLIR False Color Temperature Calibration Bar */}
                <div className="absolute right-4 top-20 bottom-20 w-5 flex flex-col items-center justify-between z-20 pointer-events-none bg-black/70 border border-slate-700/80 rounded py-2 px-1 backdrop-blur-sm">
                  <span className="text-[8px] font-mono text-white font-bold">38°</span>
                  <div className="w-2 flex-1 rounded my-1 bg-gradient-to-t from-[#1b0258] via-[#a70058] via-[#e55900] via-[#f7d100] to-[#ffffff] shadow-inner"></div>
                  <span className="text-[8px] font-mono text-cyan-300 font-bold">18°</span>
                </div>

                {/* Thermal Sensor Core Spec Pill */}
                <div className="absolute bottom-4 left-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-2.5 py-1 rounded border border-amber-500/50 text-[10px] font-mono text-amber-300 shadow-sm pointer-events-none">
                  <Flame className="w-3.5 h-3.5 text-amber-400" />
                  <span>FLIR LWIR 8-14μm · VOX CORE · SPOT: 36.8°C (DELTA +14.6°C)</span>
                </div>
              </>
            )}

            {viewMode === 'night' && (
              <>
                {/* NVG CRT Scan Reticle Overlay */}
                <div className="absolute inset-0 pointer-events-none border-[30px] border-black/40 rounded-full scale-125 opacity-40"></div>
                <div className="absolute bottom-4 left-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-2.5 py-1 rounded border border-emerald-500/50 text-[10px] font-mono text-emerald-300 shadow-sm pointer-events-none">
                  <Moon className="w-3.5 h-3.5 text-emerald-400" />
                  <span>NIGHT IR GEN-III+ · 850nm ILLUMINATOR [92%] · GAIN: +38dB</span>
                </div>
              </>
            )}

            {viewMode === 'optical' && (
              <div className="absolute bottom-4 left-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-2.5 py-1 rounded border border-blue-500/40 text-[10px] font-mono text-blue-300 shadow-sm pointer-events-none">
                <Eye className="w-3.5 h-3.5 text-blue-400" />
                <span>OPTICAL HD · SONY STARVIS II · AUTO WDR DYNAMIC BALANCED</span>
              </div>
            )}

            {/* Top Live Badges */}
            <div className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded border border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.4)]">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
              </span>
              <span className="text-xs font-mono font-bold tracking-widest text-red-100">LIVE FEED</span>
              <span className="text-[10px] font-mono text-slate-400 px-1 bg-slate-800 rounded">0.04s LATENCY</span>
            </div>

            <div className="absolute top-4 right-4 z-20 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded border border-emerald-500/40 shadow-sm">
              <SignalHigh className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span className="text-xs font-mono font-bold tracking-wider text-emerald-400">{currentCam.status}</span>
              <span className="text-[10px] font-mono text-slate-400 border-l border-slate-700 pl-2">99.8% SIGNAL</span>
            </div>

            {/* Corner Tactical Brackets */}
            <div className="absolute top-3 left-3 w-4 h-4 border-t-2 border-l-2 border-blue-400 pointer-events-none z-20"></div>
            <div className="absolute top-3 right-3 w-4 h-4 border-t-2 border-r-2 border-blue-400 pointer-events-none z-20"></div>
            <div className="absolute bottom-3 left-3 w-4 h-4 border-b-2 border-l-2 border-blue-400 pointer-events-none z-20"></div>
            <div className="absolute bottom-3 right-3 w-4 h-4 border-b-2 border-r-2 border-blue-400 pointer-events-none z-20"></div>

            {/* SVG REALISTIC GEOFENCE & TRIPWIRE POLYGON OVERLAY */}
            <svg 
              className="absolute inset-0 w-full h-full pointer-events-none z-10" 
              viewBox="0 0 100 100" 
              preserveAspectRatio="none"
            >
              {/* Shaded Geofence Polygon */}
              <polygon 
                points={currentCam.tripwirePolygon} 
                fill={currentCam.isAlert ? "rgba(239, 68, 68, 0.16)" : "rgba(59, 130, 246, 0.08)"} 
                stroke={currentCam.isAlert ? "#EF4444" : "#3B82F6"} 
                strokeWidth="0.8" 
                strokeDasharray="2.5, 1.5" 
                className={currentCam.isAlert ? "animate-pulse" : ""} 
              />

              {/* Polygon Vertex Coordinates Markers */}
              {currentCam.tripwirePoints && currentCam.tripwirePoints.map(([x, y], idx) => (
                <g key={idx}>
                  <circle 
                    cx={x * 100} 
                    cy={y * 100} 
                    r="1.0" 
                    fill={currentCam.isAlert ? "#EF4444" : "#60A5FA"} 
                    stroke="#FFFFFF" 
                    strokeWidth="0.3" 
                  />
                  <circle 
                    cx={x * 100} 
                    cy={y * 100} 
                    r="2.2" 
                    fill="none" 
                    stroke={currentCam.isAlert ? "#EF4444" : "#60A5FA"} 
                    strokeWidth="0.2" 
                    opacity="0.6" 
                  />
                </g>
              ))}
            </svg>

            {/* GEOFENCE SECTOR TAG PINNED TO POLYGON */}
            <div className={`absolute top-[40%] left-1/2 -translate-x-1/2 z-20 pointer-events-none flex items-center gap-2 px-3 py-1 rounded border shadow-lg backdrop-blur-md text-[10px] font-mono tracking-widest uppercase ${
              currentCam.isAlert 
                ? 'bg-red-950/90 text-red-200 border-red-500/70 shadow-[0_0_15px_rgba(239,68,68,0.5)]'
                : 'bg-slate-900/90 text-blue-300 border-blue-500/50'
            }`}>
              <Zap className={`w-3.5 h-3.5 ${currentCam.isAlert ? 'text-red-400 fill-red-400 animate-bounce' : 'text-blue-400'}`} />
              <span>GEOFENCE [{currentCam.sector}] // {currentCam.isAlert ? 'TRIPWIRE BREACH DETECTED' : 'ARMED & MONITORED'}</span>
            </div>

            {/* DYNAMIC AI DETECTION BOUNDING BOXES */}
            {currentCam.detections.map((d) => (
              <div
                key={d.id}
                onClick={() => handleDetectionClick(d)}
                style={{
                  position: 'absolute',
                  top: d.bbox.top,
                  left: d.bbox.left,
                  right: d.bbox.right,
                  width: d.bbox.width,
                  height: d.bbox.height
                }}
                className={`border-2 cursor-pointer z-20 hover:scale-105 transition duration-200 ${
                  d.badgeColor === 'red'
                    ? 'border-red-500 bg-red-500/15 shadow-[0_0_15px_rgba(239,68,68,0.6)]'
                    : d.badgeColor === 'amber'
                    ? 'border-amber-500 bg-amber-500/15 shadow-[0_0_15px_rgba(245,158,11,0.5)]'
                    : 'border-blue-400 bg-blue-500/15 shadow-[0_0_15px_rgba(59,130,246,0.5)]'
                }`}
                title={`Click target to open QRT Quick-Dispatch Modal (${d.label})`}
              >
                {/* Header Tag */}
                <div className={`absolute -top-7 left-[-2px] text-white font-mono font-bold text-[10px] px-2 py-0.5 flex items-center gap-1.5 shadow-md uppercase tracking-wider whitespace-nowrap ${
                  d.badgeColor === 'red' ? 'bg-red-600' : d.badgeColor === 'amber' ? 'bg-amber-600' : 'bg-blue-600'
                }`}>
                  {d.class === 'person' ? <UserX className="w-3 h-3" /> : <Truck className="w-3 h-3" />}
                  <span>{d.label}</span>
                  <span className={`text-[8px] px-1 rounded ${
                    d.badgeColor === 'red' ? 'bg-red-900 text-red-200' : 'bg-slate-900 text-slate-200'
                  }`}>
                    {d.badge}
                  </span>
                </div>

                {/* Footer Telemetry Tag */}
                <div className={`absolute -bottom-5 left-0 text-[10px] font-mono bg-black/85 px-1.5 py-0.2 rounded border whitespace-nowrap ${
                  d.badgeColor === 'red' 
                    ? 'text-red-300 border-red-500/50' 
                    : d.badgeColor === 'amber'
                    ? 'text-amber-300 border-amber-500/50'
                    : 'text-blue-300 border-blue-500/50'
                }`}>
                  {d.telemetry}
                </div>

                {/* Targeting Crosshair */}
                <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 ${
                  d.badgeColor === 'red' ? 'text-red-400/80' : 'text-blue-400/80'
                }`}>
                  <Crosshair className="w-4 h-4 animate-spin" />
                </div>
              </div>
            ))}

          </div>

          {/* Bottom Feed Control Bar */}
          <div className="h-12 bg-slate-900/95 border-t border-slate-700/80 px-3 flex items-center justify-between shrink-0">
            {/* Mode toggles */}
            <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-md border border-slate-700 text-xs font-mono">
              <button
                onClick={() => handleSelectMode('optical')}
                className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition ${
                  viewMode === 'optical' ? 'bg-blue-600 text-white font-bold shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Sun className="w-3.5 h-3.5" />
                <span>OPTICAL</span>
              </button>
              <button
                onClick={() => handleSelectMode('thermal')}
                className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition ${
                  viewMode === 'thermal' ? 'bg-amber-600 text-white font-bold shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Flame className="w-3.5 h-3.5" />
                <span>FLIR THERMAL</span>
              </button>
              <button
                onClick={() => handleSelectMode('night')}
                className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition ${
                  viewMode === 'night' ? 'bg-emerald-600 text-white font-bold shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Moon className="w-3.5 h-3.5" />
                <span>NIGHT IR</span>
              </button>
            </div>

            {/* PTZ Zoom & Quick Dispatch */}
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-slate-800 px-2 py-1 rounded border border-slate-700 text-xs font-mono">
                <button
                  onClick={() => setZoomLevel(prev => Math.max(1, +(prev - 0.25).toFixed(2)))}
                  className="p-1 hover:text-blue-400"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-slate-300 w-12 text-center font-bold">{zoomLevel.toFixed(1)}x</span>
                <button
                  onClick={() => setZoomLevel(prev => Math.min(3, +(prev + 0.25).toFixed(2)))}
                  className="p-1 hover:text-blue-400"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
              </div>

              <button
                onClick={() => {
                  playTacticalBeep(940, 0.2);
                  onSelectAlert(alerts[0]);
                }}
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
                onClick={() => handleSelectCamera(cam.id)}
                className={`flex items-center justify-between px-2.5 py-1.5 rounded border text-left font-mono transition ${
                  activeCam === cam.id
                    ? 'bg-blue-950/80 border-blue-500 text-blue-300 shadow-[0_0_12px_rgba(59,130,246,0.35)] ring-1 ring-blue-400'
                    : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <div className="truncate">
                  <div className="text-[11px] font-bold text-white truncate">{cam.name}</div>
                  <div className="text-[9px] text-slate-500">{cam.sector}</div>
                </div>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                  cam.status === 'ALERT' 
                    ? 'bg-red-950 text-red-400 border border-red-700 animate-pulse' 
                    : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
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
                    className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white font-mono text-[10px] font-bold rounded flex items-center gap-1 transition shadow-sm"
                  >
                    <span>INSPECT & DISPATCH</span>
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}

            {/* Tactical Sector Map Mini-card synchronized with current camera */}
            <div className="p-3 bg-[#0B1120] border border-slate-800 rounded-lg space-y-2">
              <div className="flex items-center justify-between text-xs font-mono text-slate-300 font-semibold border-b border-slate-800 pb-1.5">
                <span className="flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-400" />
                  {currentCam.sector} GPS TELEMETRY
                </span>
                <span className="text-emerald-400 text-[10px] flex items-center gap-1">
                  <Target className="w-3 h-3 animate-spin" />
                  RADAR LOCK
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-400">
                <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">GPS COORDINATES:</span>
                  <span className="text-white font-bold">{currentCam.telemetry.lat}° N / {currentCam.telemetry.lng}° E</span>
                </div>
                <div className="bg-slate-900/80 p-1.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">BEARING / FOV:</span>
                  <span className="text-blue-400 font-bold">{currentCam.telemetry.az} · {currentCam.telemetry.fov}</span>
                </div>
              </div>
            </div>

          </div>

        </section>

      </main>
    </div>
  );
}
