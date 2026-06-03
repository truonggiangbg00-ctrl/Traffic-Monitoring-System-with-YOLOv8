"""
model_evaluator.py: Comprehensive model evaluation and comparison

Purpose:
  Compare baseline PyTorch model vs optimized models (ONNX, TensorRT) on test set
  Measures: mAP (accuracy), FPS (speed), precision, recall, F1 score
  Generates comparison charts for performance analysis

Output:
  - Metrics CSV: predictions.json with detailed per-image results
  - Charts: Confusion matrix, P-R curves, F1-confidence curves
  - Summary: Console output with comparison table
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

try:
    from ultralytics import YOLO
    import numpy as np
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)


class ModelEvaluator:
    """Evaluate and compare YOLO models on test dataset"""
    
    def __init__(self, data_yaml: str, output_dir: str = "runs/evaluate"):
        """
        Initialize evaluator
        
        Args:
            data_yaml: Path to dataset configuration (data.yaml)
            output_dir: Directory to save evaluation results
        """
        self.data_yaml = Path(data_yaml)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.data_yaml.exists():
            raise FileNotFoundError(f"Data config not found: {data_yaml}")
        
        print(f"📊 Dataset config: {self.data_yaml}")
        print(f"📁 Output directory: {self.output_dir}\n")
        
        self.results = {}
    
    def evaluate_model(self, model_path: str, model_name: str, 
                      split: str = 'test', device: str = '0') -> Dict:
        """
        Evaluate single model on test set
        
        Args:
            model_path: Path to model file
            model_name: Name for this model (for comparison)
            split: Dataset split ('test', 'val')
            device: Device to use ('0' for GPU, 'cpu' for CPU)
        
        Returns:
            Dictionary with evaluation metrics
        """
        model_path = Path(model_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        print(f"📍 Evaluating: {model_name}")
        print(f"   Model: {model_path}")
        print(f"   Device: {device}", end="\n\n")
        
        try:
            model = YOLO(str(model_path))
            
            # Run validation
            print(f"   Running evaluation on {split} set...", end=" ", flush=True)
            eval_start = time.time()
            
            metrics = model.val(
                data=str(self.data_yaml),
                split=split,
                conf=0.25,        # Confidence threshold
                iou=0.6,          # NMS IOU threshold
                device=device,
                plots=True,       # Generate confusion matrix and PR curves
                save_json=True,   # Save results as JSON
                project=str(self.output_dir),
                name=f'{model_name}_eval',
                verbose=False
            )
            
            eval_time = time.time() - eval_start
            print(f"✓ ({eval_time:.1f}s)\n")
            
            # Extract metrics
            results = {
                'model_name': model_name,
                'model_path': str(model_path),
                'split': split,
                'device': device,
                'evaluation_time': eval_time,
                'mAP50': float(metrics.box.map50) if hasattr(metrics.box, 'map50') else 0,
                'mAP50_95': float(metrics.box.map) if hasattr(metrics.box, 'map') else 0,
                'precision': float(metrics.box.p.mean()) if hasattr(metrics.box, 'p') else 0,
                'recall': float(metrics.box.r.mean()) if hasattr(metrics.box, 'r') else 0,
                'fitness': float(metrics.fitness) if hasattr(metrics, 'fitness') else 0
            }
            
            # Calculate F1 score
            if results['precision'] > 0 and results['recall'] > 0:
                results['f1'] = 2 * (results['precision'] * results['recall']) / \
                               (results['precision'] + results['recall'])
            else:
                results['f1'] = 0
            
            self.results[model_name] = results
            return results
        
        except Exception as e:
            print(f"\n❌ Evaluation failed for {model_name}: {e}")
            raise
    
    def estimate_fps(self, model_path: str, model_name: str, 
                    imgsz: int = 640, device: str = '0', 
                    num_frames: int = 100) -> float:
        """
        Estimate inference speed (FPS)
        
        Args:
            model_path: Path to model file
            model_name: Name for logging
            imgsz: Input image size
            device: Device to use
            num_frames: Number of frames to benchmark
        
        Returns:
            Frames per second (FPS)
        """
        model_path = Path(model_path)
        
        print(f"⚡ Benchmarking FPS: {model_name}")
        print(f"   Input size: {imgsz}x{imgsz}")
        print(f"   Frames: {num_frames}", end=" ... ", flush=True)
        
        try:
            model = YOLO(str(model_path))
            
            # Create dummy input
            dummy_img = np.random.randint(0, 255, (imgsz, imgsz, 3), dtype=np.uint8)
            
            # Warmup
            for _ in range(5):
                _ = model(dummy_img, verbose=False)
            
            # Benchmark
            start_time = time.time()
            for _ in range(num_frames):
                _ = model(dummy_img, verbose=False)
            
            elapsed = time.time() - start_time
            fps = num_frames / elapsed
            
            print(f"✓ {fps:.1f} FPS\n")
            
            # Store FPS in results
            if model_name in self.results:
                self.results[model_name]['fps'] = fps
            else:
                self.results[model_name] = {'fps': fps}
            
            return fps
        
        except Exception as e:
            print(f"\n⚠ FPS estimation failed: {e}")
            return 0
    
    def print_comparison_table(self):
        """Print comparison table of all evaluated models"""
        if not self.results:
            print("No results to display")
            return
        
        print("\n" + "="*100)
        print("📊 MODEL COMPARISON RESULTS")
        print("="*100)
        
        # Print header
        print(f"{'Model':<20} {'mAP50':<8} {'mAP50-95':<10} {'Precision':<10} {'Recall':<10} {'F1':<8} {'FPS':<8}")
        print("-"*100)
        
        # Print results for each model
        for name, metrics in self.results.items():
            print(f"{name:<20} {metrics.get('mAP50', 0):<8.4f} "
                  f"{metrics.get('mAP50_95', 0):<10.4f} {metrics.get('precision', 0):<10.4f} "
                  f"{metrics.get('recall', 0):<10.4f} {metrics.get('f1', 0):<8.4f} "
                  f"{metrics.get('fps', 0):<8.1f}")
        
        print("="*100 + "\n")
    
    def save_results_json(self):
        """Save comparison results to JSON file"""
        output_file = self.output_dir / "comparison_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
    
    def compare_baseline_vs_optimized(self, baseline_path: str, 
                                     optimized_paths: Dict[str, str]):
        """
        Compare baseline model against optimized versions
        
        Args:
            baseline_path: Path to baseline PyTorch model
            optimized_paths: Dict mapping model name to path
                           {'onnx': path, 'tensorrt': path, ...}
        """
        print("\n" + "="*100)
        print("🚀 BASELINE vs OPTIMIZED MODEL COMPARISON")
        print("="*100 + "\n")
        
        # Evaluate baseline
        self.evaluate_model(baseline_path, 'Baseline-PT', device='0')
        self.estimate_fps(baseline_path, 'Baseline-PT', device='0')
        
        # Evaluate optimized models
        for opt_name, opt_path in optimized_paths.items():
            if Path(opt_path).exists():
                try:
                    self.evaluate_model(opt_path, f'Optimized-{opt_name.upper()}', device='0')
                    self.estimate_fps(opt_path, f'Optimized-{opt_name.upper()}', device='0')
                except Exception as e:
                    print(f"⚠ Skipped {opt_name}: {e}\n")
        
        # Print summary
        self.print_comparison_table()
        self.save_results_json()


def main():
    """Command-line interface for model evaluation"""
    parser = argparse.ArgumentParser(
        description='Evaluate and compare YOLO models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python model_evaluator.py                          # Use default configs
  python model_evaluator.py --data Data/data.yaml    # Custom dataset
  python model_evaluator.py --baseline model.pt      # Evaluate single model
        """
    )
    
    parser.add_argument('--data', default='../Data/data.yaml',
                       help='Path to dataset config (data.yaml)')
    parser.add_argument('--baseline', default='../weights/yolo_basic.pt',
                       help='Path to baseline model')
    parser.add_argument('--optimized-onnx', default='../weights/yolo_optimized.onnx',
                       help='Path to ONNX optimized model')
    parser.add_argument('--optimized-tensorrt', default='../weights/yolo_optimized.engine',
                       help='Path to TensorRT optimized model')
    parser.add_argument('--output-dir', default='runs/evaluate',
                       help='Output directory for results')
    parser.add_argument('--device', default='0',
                       help='Device to use (0 for GPU, cpu for CPU)')
    
    args = parser.parse_args()
    
    try:
        evaluator = ModelEvaluator(
            data_yaml=args.data,
            output_dir=args.output_dir
        )
        
        # Compare models
        optimized_models = {}
        if Path(args.optimized_onnx).exists():
            optimized_models['onnx'] = args.optimized_onnx
        if Path(args.optimized_tensorrt).exists():
            optimized_models['tensorrt'] = args.optimized_tensorrt
        
        evaluator.compare_baseline_vs_optimized(
            baseline_path=args.baseline,
            optimized_paths=optimized_models
        )
        
        print("✅ Evaluation completed successfully!")
    
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()