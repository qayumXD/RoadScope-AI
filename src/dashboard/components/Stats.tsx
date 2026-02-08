import React from 'react';
import { Pothole } from '../types';

interface StatsProps {
    potholes: Pothole[];
    className?: string;
}

export default function PotholeStats({ potholes, className }: StatsProps) {
    const total = potholes.length;
    const large = potholes.filter(p => p.severity === 'Large').length;
    const medium = potholes.filter(p => p.severity === 'Medium').length;
    const small = potholes.filter(p => p.severity === 'Small').length;

    return (
        <div className={`grid grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
            <StatCard title="Total Detected" value={total} color="bg-blue-50 text-blue-700" />
            <StatCard title="Large / Critical" value={large} color="bg-red-50 text-red-700" />
            <StatCard title="Medium Priority" value={medium} color="bg-orange-50 text-orange-700" />
            <StatCard title="Small / Monitor" value={small} color="bg-yellow-50 text-yellow-700" />
        </div>
    );
}

const StatCard = ({ title, value, color }: { title: string; value: number; color: string }) => (
    <div className={`p-4 rounded-xl shadow-sm border border-gray-100 ${color}`}>
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">{title}</h3>
        <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
);
