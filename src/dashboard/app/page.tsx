'use client';

import { useState, useEffect } from 'react';
import Papa from 'papaparse';
import { UploadCloud, Map as MapIcon, Loader2, Database } from 'lucide-react';
import PotholeMap from '../components/Map';
import PotholeStats from '../components/Stats';
import { Pothole } from '../types';

export default function Home() {
  const [potholes, setPotholes] = useState<Pothole[]>([]);
  const [filterSeverity, setFilterSeverity] = useState<'All' | 'Small' | 'Medium' | 'Large'>('All');
  const [isLoading, setIsLoading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  // Filtered data for display
  const filteredPotholes = potholes.filter(p => 
    filterSeverity === 'All' ? true : p.severity === filterSeverity
  );

  // Auto-load default data if present in public folder
  useEffect(() => {
    const loadDefaultData = async () => {
      try {
        const response = await fetch('/potholes.csv');
        if (response.ok) {
          const text = await response.text();
          setFileName('potholes.csv (Auto-loaded)');
          parseCSV(text);
        }
      } catch (err) {
        console.log('No default potholes.csv found in public folder.');
      }
    };
    loadDefaultData();
  }, []);

  const parseCSV = (csvText: string) => {
    setIsLoading(true);
    Papa.parse(csvText, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const parsedData: Pothole[] = results.data.map((row: any) => ({
          id: row.pothole_id || Math.random().toString(36).substr(2, 9),
          latitude: parseFloat(row.latitude),
          longitude: parseFloat(row.longitude),
          severity: row.severity as 'Small' | 'Medium' | 'Large',
          confidence: parseFloat(row.confidence),
          timestamp: row.time || row.timestamp_ms || new Date().toISOString(),
          frame_id: parseInt(row.frame_id),
        })).filter(p => !isNaN(p.latitude) && !isNaN(p.longitude));

        setPotholes(parsedData);
        setIsLoading(false);
      },
      error: (error) => {
        console.error('Error parsing CSV:', error);
        setIsLoading(false);
      }
    });
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        parseCSV(e.target.result as string);
      }
    };
    reader.readAsText(file);
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 p-2 rounded-lg text-white">
            <MapIcon size={24} />
          </div>
          <h1 className="text-xl font-bold text-gray-900">RoadScope AI</h1>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors shadow-sm">
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : <UploadCloud size={20} />}
            <span className="text-sm font-medium text-gray-700">
              {fileName ? fileName : 'Upload CSV'}
            </span>
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:flex-row h-[calc(100vh-73px)] overflow-hidden">
        {/* Sidebar / Stats (Mobile: Top, Desktop: Left) */}
        <div className="lg:w-96 w-full bg-white border-r border-gray-200 p-6 overflow-y-auto flex-shrink-0 z-10 shadow-[4px_0_24px_rgba(0,0,0,0.02)]">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-2">Analysis Overview</h2>
            <p className="text-sm text-gray-500">
              Upload your `mapped_potholes.csv` to visualize detected road hazards.
            </p>
          </div>

          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Severity Filter</h3>
            <div className="flex gap-2">
              {(['All', 'Small', 'Medium', 'Large'] as const).map((sev) => (
                <button
                  key={sev}
                  onClick={() => setFilterSeverity(sev)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                    filterSeverity === sev
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>

          <PotholeStats potholes={filteredPotholes} className="grid-cols-2 gap-3 mb-6" />

          {filteredPotholes.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Detections</h3>
              <div className="space-y-3">
                {filteredPotholes.slice(0, 10).map((p) => (
                  <div key={p.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer border border-gray-100">
                    <div className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${p.severity === 'Large' ? 'bg-red-500' :
                        p.severity === 'Medium' ? 'bg-orange-500' : 'bg-yellow-500'
                      }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Pothole #{p.id}</p>
                      <p className="text-xs text-gray-500">{new Date(p.timestamp).toLocaleTimeString()}</p>
                      <div className="flex gap-2 mt-1">
                        <span className="text-[10px] font-mono bg-white px-1.5 py-0.5 rounded border border-gray-200 text-gray-600">
                          Conf: {Math.round(p.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Map Area */}
        <div className="flex-1 relative bg-gray-200">
          <PotholeMap potholes={filteredPotholes} className="h-full w-full rounded-none" />

          {filteredPotholes.length === 0 && !isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-50/80 backdrop-blur-sm z-0 pointer-events-none">
              <div className="text-center p-8">
                <div className="bg-white p-4 rounded-full inline-block shadow-md mb-4">
                  <Database size={48} className="text-blue-500" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900">No {filterSeverity !== 'All' ? filterSeverity : ''} Data Found</h3>
                <p className="text-gray-500 mt-2 max-w-sm mx-auto">
                  {potholes.length === 0 
                    ? "Upload a processed CSV file to see detections on the map."
                    : `There are no ${filterSeverity} potholes detected in this dataset.`}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
