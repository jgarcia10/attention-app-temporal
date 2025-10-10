"""
Main processing pipeline that coordinates detection, head pose estimation, and tracking
"""
import cv2
import numpy as np
import os
from typing import List, Dict, Any, Tuple

from .detector import PersonDetector
from .head_pose import HeadPoseEstimator
from .tracker import PersonTracker
from .utils import draw_overlays, count_statuses, add_stats_overlay, resize_frame


class AttentionPipeline:
    def __init__(self, 
                 model_path: str = "./models/yolov8n.pt",
                 conf_threshold: float = 0.4,
                 yaw_threshold: float = 25.0,
                 pitch_threshold: float = 20.0,
                 iou_threshold: float = 0.3):
        """
        Initialize the attention detection pipeline
        
        Args:
            model_path: Path to YOLO model
            conf_threshold: YOLO confidence threshold
            yaw_threshold: Head yaw threshold for attention classification
            pitch_threshold: Head pitch threshold for attention classification
            iou_threshold: IoU threshold for tracking
        """
        self.detector = PersonDetector(model_path, conf_threshold)
        self.head_pose_estimator = HeadPoseEstimator(yaw_threshold, pitch_threshold)
        self.tracker = PersonTracker(iou_threshold)
        
        # Statistics
        self.frame_count = 0
        self.recent_stats = []  # Rolling stats for live display
        self.max_recent_stats = 60  # Keep last 60 frames of stats
    
    def process_frame(self, frame: np.ndarray, 
                     target_width: int = None, 
                     target_height: int = None) -> Tuple[np.ndarray, Dict[str, int]]:
        """
        Process a single frame through the complete pipeline - Optimized for Windows
        
        Args:
            frame: Input frame
            target_width: Optional target width for output
            target_height: Optional target height for output
            
        Returns:
            Tuple of (annotated_frame, stats_dict)
        """
        self.frame_count += 1
        
        # Resize input frame if needed (for processing efficiency)
        processing_frame = frame.copy()
        original_height, original_width = frame.shape[:2]
        
        # Optimize processing resolution for Windows performance
        if target_width and target_height:
            # If target resolution is very small, use it directly for processing
            if target_width <= 320 and target_height <= 240:
                processing_frame = cv2.resize(frame, (target_width, target_height))
            else:
                # Use a reasonable processing resolution for better performance
                processing_frame = cv2.resize(frame, (320, 240))
        
        # Step 1: Detect persons
        detections = self.detector.detect(processing_frame)
        
        # Step 2: Analyze head pose for each detection
        processed_detections = []
        
        for detection in detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = bbox
            
            # Extract ROI
            roi = processing_frame[y1:y2, x1:x2]
            
            if roi.size == 0:  # Skip invalid ROIs
                continue
            
            # Get face landmarks
            face_landmarks = self.head_pose_estimator.get_face_landmarks(roi)
            
            if face_landmarks is None:
                # No face detected - red status
                status = "No face detected"
                head_vector = None
                yaw, pitch = 0.0, 0.0
            else:
                # Estimate head pose
                yaw, pitch = self.head_pose_estimator.estimate_head_pose(
                    face_landmarks, roi.shape
                )
                
                # Classify attention status using raw angles (smoothing will be applied after tracking)
                # Note: person_id will be available after tracking, so we'll re-classify then
                status = self.head_pose_estimator.classify_attention(yaw, pitch)
                
                # Get direction vector for arrow overlay using raw angles
                head_vector = self.head_pose_estimator.get_direction_vector(yaw, pitch)
            
            # Add processed information to detection
            detection.update({
                'status': status,
                'head_vector': head_vector,
                'yaw': yaw,
                'pitch': pitch
            })
            
            processed_detections.append(detection)
        
        # Step 3: Update tracker with processed detections
        tracked_detections = self.tracker.update(processed_detections)
        
        # Clean up pose history for disappeared tracks
        disappeared_track_ids = self.tracker.get_disappeared_track_ids()
        for track_id in disappeared_track_ids:
            self.head_pose_estimator.clear_history(track_id)
        
        # Step 4: Apply temporal smoothing using actual person IDs
        for detection in tracked_detections:
            person_id = detection.get('id')
            if person_id is not None:
                if detection.get('head_vector') is not None:
                    # Apply smoothing using the actual person ID from tracker
                    smoothed_yaw, smoothed_pitch = self.head_pose_estimator.smooth_pose(
                        person_id, detection['yaw'], detection['pitch']
                    )
                    
                    # Update with smoothed values
                    detection['yaw'] = smoothed_yaw
                    detection['pitch'] = smoothed_pitch
                    
                    # Re-classify attention status using smoothed angles and person ID for confidence tracking
                    detection['status'] = self.head_pose_estimator.classify_attention(smoothed_yaw, smoothed_pitch, person_id)
                    
                    # Add attention confidence for debugging/monitoring
                    detection['attention_confidence'] = self.head_pose_estimator.get_attention_confidence(person_id)
                    
                    # Update direction vector with smoothed angles
                    detection['head_vector'] = self.head_pose_estimator.get_direction_vector(smoothed_yaw, smoothed_pitch)
                else:
                    # Face detection failed, but we have a tracked person
                    # Use last known pose for continuity
                    last_yaw, last_pitch = self.head_pose_estimator.get_last_known_pose(person_id)
                    if last_yaw != 0.0 or last_pitch != 0.0:
                        detection['yaw'] = last_yaw
                        detection['pitch'] = last_pitch
                        detection['status'] = self.head_pose_estimator.classify_attention(last_yaw, last_pitch, person_id)
                        detection['head_vector'] = self.head_pose_estimator.get_direction_vector(last_yaw, last_pitch)
        
        # Step 5: Count statistics
        stats = count_statuses(tracked_detections)
        # Note: timestamp will be set by the API endpoint with current time
        
        # Update recent stats
        self.recent_stats.append(stats)
        if len(self.recent_stats) > self.max_recent_stats:
            self.recent_stats.pop(0)
        
        # Step 6: Draw annotations
        annotated_frame = draw_overlays(processing_frame, tracked_detections)
        annotated_frame = add_stats_overlay(annotated_frame, stats)
        
        # Step 7: Resize output if requested (optimized for Windows)
        if target_width and target_height:
            # Only resize if the processing frame was different from target
            if processing_frame.shape[:2] != (target_height, target_width):
                annotated_frame = resize_frame(annotated_frame, target_width, target_height)
        
        return annotated_frame, stats
    
    def get_recent_stats(self, seconds: int = 10) -> List[Dict[str, int]]:
        """
        Get recent statistics for the last N seconds
        
        Args:
            seconds: Number of seconds of stats to return
            
        Returns:
            List of recent stats dictionaries
        """
        # Assuming ~20 FPS, calculate how many frames to return
        frames_to_return = min(seconds * 20, len(self.recent_stats))
        return self.recent_stats[-frames_to_return:] if frames_to_return > 0 else []
    
    def get_average_stats(self, seconds: int = 10) -> Dict[str, float]:
        """
        Get average statistics over the last N seconds
        
        Args:
            seconds: Number of seconds to average over
            
        Returns:
            Dictionary with average counts and percentages
        """
        recent = self.get_recent_stats(seconds)
        
        if not recent:
            return {"green": 0, "yellow": 0, "red": 0, "total": 0, 
                   "green_pct": 0, "yellow_pct": 0, "red_pct": 0}
        
        # Calculate averages
        avg_green = sum(stat['green'] for stat in recent) / len(recent)
        avg_yellow = sum(stat['yellow'] for stat in recent) / len(recent)
        avg_red = sum(stat['red'] for stat in recent) / len(recent)
        avg_total = sum(stat['total'] for stat in recent) / len(recent)
        
        # Calculate percentages
        green_pct = (avg_green / avg_total * 100) if avg_total > 0 else 0
        yellow_pct = (avg_yellow / avg_total * 100) if avg_total > 0 else 0
        red_pct = (avg_red / avg_total * 100) if avg_total > 0 else 0
        
        return {
            "green": avg_green,
            "yellow": avg_yellow,
            "red": avg_red,
            "total": avg_total,
            "green_pct": green_pct,
            "yellow_pct": yellow_pct,
            "red_pct": red_pct
        }
    
    def reset(self):
        """Reset pipeline state"""
        self.tracker.reset()
        self.head_pose_estimator.clear_history()
        self.frame_count = 0
        self.recent_stats = []

