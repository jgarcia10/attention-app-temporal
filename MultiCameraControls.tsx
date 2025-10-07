import React, { useState, useEffect } from 'react';
import { Play, Square, Camera, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { apiService, type Config, type CameraInfo } from '../lib/api';

interface MultiCameraControlsProps {
  config: Config | null;
  isStreaming: boolean;
  onStartStream: (url: string) => void;
  onStopStream: () => void;
  onConfigUpdate: (config: Config) => void;
  onError: (error: string) => void;
}

const MultiCameraControls: React.FC<MultiCameraControlsProps> = ({
  config,
  isStreaming,
  onStartStream,
  onStopStream,
  onConfigUpdate,
  onError,
}) => {
  const [availableCameras, setAvailableCameras] = useState<CameraInfo[]>([]);
  const [selectedCameras, setSelectedCameras] = useState<number[]>([]);
  const [isDetecting, setIsDetecting] = useState(false);
  const [streamConfig, setStreamConfig] = useState({
    width: 640,
    height: 480,
    fps: 20,
  });

  // Detect available cameras on component mount
  useEffect(() => {
    detectCameras();
  }, []);

  const detectCameras = async () => {
    setIsDetecting(true);
    try {
      console.log('🔍 Starting camera detection...');
      
      // Add timeout handling
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Camera detection timeout after 120 seconds')), 120000);
      });
      
      const detectionPromise = apiService.getAvailableCameras();
      
      const response = await Promise.race([detectionPromise, timeoutPromise]);
      console.log('📹 Camera detection response:', response);
      
      setAvailableCameras(response.cameras);
      console.log(`✅ Found ${response.cameras.length} cameras:`, response.cameras);
      
      // Auto-select first available camera if none selected
      if (selectedCameras.length === 0 && response.cameras.length > 0) {
        setSelectedCameras([response.cameras[0].id]);
        console.log(`🎯 Auto-selected camera ${response.cameras[0].id}`);
      }
    } catch (error) {
      console.error('❌ Camera detection error:', error);
      if (error.message.includes('timeout')) {
        onError('Camera detection is taking too long (2+ minutes). Some cameras may need more time to initialize. Please try again or check if cameras are being used by other applications.');
      } else {
        onError(`Failed to detect cameras: ${error.message || error}`);
      }
    } finally {
      setIsDetecting(false);
    }
  };

  const testCamera = async (cameraId: number) => {
    try {
      const response = await apiService.testCamera(cameraId);
      // Update camera info in the list
      setAvailableCameras(prev => 
        prev.map(cam => 
          cam.id === cameraId 
            ? { ...cam, ...response.info, available: response.available }
            : cam
        )
      );
    } catch (error) {
      console.error('Camera test error:', error);
    }
  };

  const handleCameraSelection = (cameraId: number, checked: boolean) => {
    if (checked) {
      setSelectedCameras(prev => [...prev, cameraId]);
    } else {
      setSelectedCameras(prev => prev.filter(id => id !== cameraId));
    }
  };

  const handleStartStream = async () => {
    if (selectedCameras.length === 0) {
      onError('Please select at least one camera');
      return;
    }

    try {
      // Start multi-camera streaming
      const result = await apiService.startMultiCamera(
        selectedCameras,
        streamConfig.width,
        streamConfig.height,
        streamConfig.fps
      );

      if (result.failed_cameras.length > 0) {
        onError(`Failed to start cameras: ${result.failed_cameras.join(', ')}`);
      }

      if (result.started_cameras.length > 0) {
        const streamUrl = apiService.getMultiCameraStreamUrl(
          result.started_cameras,
          streamConfig.width,
          streamConfig.height,
          streamConfig.fps
        );
        onStartStream(streamUrl);
      }
    } catch (error) {
      onError('Failed to start multi-camera stream');
      console.error('Start stream error:', error);
    }
  };

  const handleConfigUpdate = async (updates: Partial<Config>) => {
    if (!config) return;

    try {
      const updatedConfig = await apiService.updateConfig(updates);
      onConfigUpdate(updatedConfig);
    } catch (error) {
      onError('Failed to update configuration');
      console.error('Config update error:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Multi-Camera Controls</h3>
          <button
            onClick={detectCameras}
            disabled={isDetecting}
            className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${isDetecting ? 'animate-spin' : ''}`} />
            {isDetecting ? 'Detecting...' : 'Refresh'}
          </button>
        </div>

        {/* Camera Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-gray-700">
              Available Cameras ({availableCameras.length} found)
            </label>
            <button
              onClick={detectCameras}
              disabled={isDetecting}
              className="flex items-center space-x-1 px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`h-3 w-3 ${isDetecting ? 'animate-spin' : ''}`} />
              <span>{isDetecting ? 'Scanning...' : 'Refresh'}</span>
            </button>
          </div>
          
          {isDetecting ? (
            <div className="text-sm text-blue-600 py-4 text-center">
              🔍 Scanning for cameras... Please wait.
            </div>
          ) : availableCameras.length === 0 ? (
            <div className="text-sm text-red-500 py-4 text-center border border-red-200 rounded-md bg-red-50">
              ❌ No cameras detected. 
              <br />
              <span className="text-xs text-gray-600 mt-1 block">
                Make sure your camera is connected and not being used by another application.
              </span>
            </div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {availableCameras.map((camera) => (
                <div key={camera.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-md">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id={`camera-${camera.id}`}
                      checked={selectedCameras.includes(camera.id)}
                      onChange={(e) => handleCameraSelection(camera.id, e.target.checked)}
                      disabled={!camera.available}
                      className="mr-3"
                    />
                    <Camera className="h-4 w-4 mr-2 text-gray-500" />
                    <div>
                      <label htmlFor={`camera-${camera.id}`} className="text-sm font-medium text-gray-900">
                        {camera.name}
                      </label>
                      {camera.available && (
                        <div className="text-xs text-gray-500">
                          {camera.width}x{camera.height} @ {camera.fps} FPS
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {camera.available ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <button
                      onClick={() => testCamera(camera.id)}
                      className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    >
                      Test
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Stream Settings */}
        <div className="mt-6 space-y-4">
          <h4 className="text-sm font-medium text-gray-900">Stream Settings</h4>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Width
              </label>
              <input
                type="number"
                value={streamConfig.width}
                onChange={(e) =>
                  setStreamConfig({
                    ...streamConfig,
                    width: parseInt(e.target.value) || 640,
                  })
                }
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Height
              </label>
              <input
                type="number"
                value={streamConfig.height}
                onChange={(e) =>
                  setStreamConfig({
                    ...streamConfig,
                    height: parseInt(e.target.value) || 480,
                  })
                }
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              FPS
            </label>
            <input
              type="number"
              value={streamConfig.fps}
              onChange={(e) =>
                setStreamConfig({
                  ...streamConfig,
                  fps: parseInt(e.target.value) || 20,
                })
              }
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Control Buttons */}
        <div className="mt-6">
          {!isStreaming ? (
            <button
              onClick={handleStartStream}
              disabled={selectedCameras.length === 0}
              className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="h-4 w-4 mr-2" />
              Start Multi-Camera Stream ({selectedCameras.length} cameras)
            </button>
          ) : (
            <button
              onClick={onStopStream}
              className="w-full flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <Square className="h-4 w-4 mr-2" />
              Stop Multi-Camera Stream
            </button>
          )}
        </div>
      </div>

      {/* Detection Thresholds */}
      {config && (
        <div className="pt-6 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-4">
            Detection Thresholds
          </h4>
          
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Yaw Threshold (°)
              </label>
              <input
                type="number"
                value={config.yaw_threshold}
                onChange={(e) =>
                  handleConfigUpdate({
                    yaw_threshold: parseFloat(e.target.value) || 25,
                  })
                }
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Pitch Threshold (°)
              </label>
              <input
                type="number"
                value={config.pitch_threshold}
                onChange={(e) =>
                  handleConfigUpdate({
                    pitch_threshold: parseFloat(e.target.value) || 20,
                  })
                }
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Confidence Threshold
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                max="1.0"
                value={config.conf_threshold}
                onChange={(e) =>
                  handleConfigUpdate({
                    conf_threshold: parseFloat(e.target.value) || 0.4,
                  })
                }
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MultiCameraControls;
