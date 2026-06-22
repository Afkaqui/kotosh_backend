export interface MlBehaviorEntry {
  frame: number;
  timestamp: number;
  behavior: string;
  confidence: number;
}

export interface MlAnimalResult {
  track_id: number;
  label: string;
  confidence: number;
  eating_seconds: number;
  resting_seconds: number;
  moving_seconds: number;
  total_seconds: number;
  behavior_log: MlBehaviorEntry[];
}

export interface MlAnalysisResponse {
  fps: number;
  total_frames: number;
  processed_frames: number;
  animals: MlAnimalResult[];
}
