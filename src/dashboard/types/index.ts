export interface Pothole {
    id: string;
    latitude: number;
    longitude: number;
    severity: 'Small' | 'Medium' | 'Large';
    confidence: number;
    timestamp: string;
    image_url?: string;
    frame_id?: number;
}
