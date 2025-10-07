import axios from 'axios';

// API base URL - adjust based on environment
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 180000, // Extended timeout for camera detection (3 minutes)
});

// Types
export interface StreamSource {
  source: 'webcam' | 'rtsp' | 'file';
  path?: string;
  width?: number;
  height?: number;
  fps?: number;
}

export interface Stats {
  green: number;
  yellow: number;
  red: number;
  total: number;
  timestamp: number;
  green_pct?: number;
  yellow_pct?: number;
  red_pct?: number;
}

export interface JobStatus {
  job_id: string;
  state: 'pending' | 'running' | 'done' | 'error';
  progress: number;
  error?: string;
  created_at: number;
  started_at?: number;
  completed_at?: number;
}

export interface Config {
  yolo_model_path: string;
  conf_threshold: number;
  yaw_threshold: number;
  pitch_threshold: number;
  stream_width: number;
  stream_height: number;
  stream_fps: number;
}

export interface ConfigUpdate {
  conf_threshold?: number;
  yaw_threshold?: number;
  pitch_threshold?: number;
  stream_width?: number;
  stream_height?: number;
  stream_fps?: number;
}

export interface CameraInfo {
  id: number;
  name: string;
  width: number;
  height: number;
  fps: number;
  available: boolean;
  error?: string;
}

export interface MultiCameraStats {
  active_cameras: number[];
  camera_count: number;
  aggregated_stats: Stats;
  individual_stats: { [cameraId: number]: Stats };
  timestamp: number;
}

export interface RecordingInfo {
  recording_id: string;
  stream_type: 'single' | 'multi';
  width: number;
  height: number;
  fps: number;
  message: string;
  timestamp: number;
}

export interface RecordingSummary {
  recording_id: string;
  filepath: string;
  duration: number;
  frame_count: number;
  width: number;
  height: number;
  fps: number;
  camera_ids?: number[];
  num_cameras?: number;
  file_size: number;
}

export interface RecordingStatus {
  stream_type: 'single' | 'multi';
  active_recordings: string[];
  recording_count: number;
  timestamp: number;
}

// API functions
export const apiService = {
  // Health check
  async getHealth() {
    const response = await api.get('/health');
    return response.data;
  },

  // Configuration
  async getConfig(): Promise<Config> {
    const response = await api.get('/config');
    return response.data;
  },

  async updateConfig(config: ConfigUpdate): Promise<Config> {
    const response = await api.put('/config', config);
    return response.data;
  },

  // Streaming
  getStreamUrl(params: StreamSource): string {
    const queryParams = new URLSearchParams();
    queryParams.append('source', params.source);
    if (params.path) queryParams.append('path', params.path);
    if (params.width) queryParams.append('w', params.width.toString());
    if (params.height) queryParams.append('h', params.height.toString());
    if (params.fps) queryParams.append('fps', params.fps.toString());

    return `${API_BASE_URL}/api/stream?${queryParams.toString()}`;
  },

  async stopStream() {
    const response = await api.post('/stream/stop');
    return response.data;
  },

  // Video upload and processing
  async uploadVideo(file: File): Promise<{ job_id: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await api.get(`/job/${jobId}/status`);
    return response.data;
  },

  getJobResultUrl(jobId: string): string {
    return `${API_BASE_URL}/api/job/${jobId}/result`;
  },

  // Statistics
  async getLiveStats(): Promise<Stats> {
    const response = await api.get('/stats/live');
    return response.data;
  },

  async getAverageStats(seconds: number = 10): Promise<Stats> {
    const response = await api.get(`/stats/average?seconds=${seconds}`);
    return response.data;
  },

  // Multi-camera functionality
  async getAvailableCameras(): Promise<{ cameras: CameraInfo[]; count: number; timestamp: number }> {
    const response = await api.get('/cameras');
    return response.data;
  },

  async getAllAvailableCameras(): Promise<{ cameras: CameraInfo[]; count: number; timestamp: number }> {
    const response = await api.get('/cameras/full');
    return response.data;
  },

  async testCamera(cameraId: number): Promise<{ camera_id: number; available: boolean; info: CameraInfo; timestamp: number }> {
    const response = await api.get(`/cameras/${cameraId}/test`);
    return response.data;
  },

  getMultiCameraStreamUrl(cameraIds: number[], width: number = 640, height: number = 480, fps: number = 20): string {
    const queryParams = new URLSearchParams();
    queryParams.append('cameras', cameraIds.join(','));
    queryParams.append('w', width.toString());
    queryParams.append('h', height.toString());
    queryParams.append('fps', fps.toString());

    return `${API_BASE_URL}/api/multi-camera/stream?${queryParams.toString()}`;
  },

  async startMultiCamera(cameras: number[], width: number = 640, height: number = 480, fps: number = 20): Promise<{ started_cameras: number[]; failed_cameras: number[]; message: string; timestamp: number }> {
    const response = await api.post('/multi-camera/start', {
      cameras,
      width,
      height,
      fps
    });
    return response.data;
  },

  async stopMultiCamera(cameras?: number[]): Promise<{ stopped_cameras?: number[]; message: string; timestamp: number }> {
    const response = await api.post('/multi-camera/stop', {
      cameras: cameras || []
    });
    return response.data;
  },

  async getMultiCameraStatus(): Promise<MultiCameraStats> {
    const response = await api.get('/multi-camera/status');
    return response.data;
  },

  // Recording functions
  async startRecording(recordingId: string, streamType: 'single' | 'multi', width: number = 1280, height: number = 720, fps: number = 20, customName?: string): Promise<RecordingInfo> {
    const response = await api.post('/recording/start', {
      recording_id: recordingId,
      stream_type: streamType,
      width,
      height,
      fps,
      custom_name: customName
    });
    return response.data;
  },

  async stopRecording(recordingId: string, streamType: 'single' | 'multi'): Promise<{ recording_id: string; stream_type: string; summary: RecordingSummary; message: string; timestamp: number }> {
    const response = await api.post('/recording/stop', {
      recording_id: recordingId,
      stream_type: streamType
    });
    return response.data;
  },

  async getRecordingStatus(streamType: 'single' | 'multi'): Promise<RecordingStatus> {
    const response = await api.get(`/recording/status?stream_type=${streamType}`);
    return response.data;
  },

  // Report functions
  async generateReport(recordingId: string, streamType: 'single' | 'multi'): Promise<{ recording_id: string; stream_type: string; report_path: string; message: string; timestamp: number }> {
    const response = await api.post('/report/generate', {
      recording_id: recordingId,
      stream_type: streamType
    });
    return response.data;
  },

  getReportDownloadUrl(filename: string): string {
    return `${API_URL}/api/report/download/${filename}`;
  },
};

export default apiService;

