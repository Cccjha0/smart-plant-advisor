import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Leaf } from 'lucide-react';
import { OverviewTab } from './plant-tabs/OverviewTab';
import { MetricsTab } from './plant-tabs/MetricsTab';
import { ReportsTab } from './plant-tabs/ReportsTab';
import { PhotosTab } from './plant-tabs/PhotosTab';
import { DreamTab } from './plant-tabs/DreamTab';
import { api, Plant } from '../utils/api';

export function PlantDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const plantIdNum = Number(id);
  const [plants, setPlants] = useState<Plant[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const load = async () => {
      try {
        const list = await api.getPlants().catch(() => []);
        setPlants(list || []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const plant = useMemo(() => plants.find((p) => p.id === plantIdNum), [plants, plantIdNum]);

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'metrics', label: 'Live Data' },
    { id: 'reports', label: 'Reports' },
    { id: 'photos', label: 'Photos' },
    { id: 'dreams', label: 'Dream Garden' },
  ];

  if (loading) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!plant) {
    return (
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-500">Plant not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to overview</span>
          </button>

          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-green-100 rounded-xl flex items-center justify-center">
              <Leaf className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <h1 className="text-gray-900">{plant.nickname || 'Unnamed'}</h1>
              <p className="text-gray-500">{plant.species || 'Species not set'}</p>
            </div>
          </div>
        </div>

        <div className="border-b border-gray-200 mb-6">
          <nav className="flex gap-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`pb-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-green-500 text-green-700'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div>
          {activeTab === 'overview' && <OverviewTab plant={plant} />}
          {activeTab === 'metrics' && <MetricsTab plantId={plant.id} />}
          {activeTab === 'reports' && <ReportsTab plantId={plant.id} />}
          {activeTab === 'photos' && <PhotosTab plantId={plant.id} />}
          {activeTab === 'dreams' && <DreamTab plantId={plant.id} plantName={plant.nickname || `Plant #${plant.id}`} />}
        </div>
      </div>
    </div>
  );
}
