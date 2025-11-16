#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Visual comparison module for screenshots.

Compares screenshots between test runs to detect visual regressions.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class VisualComparison:
    """Compares screenshots visually."""
    
    def __init__(self, baseline_dir: Path, current_dir: Path, diff_dir: Optional[Path] = None):
        """
        Initialize visual comparison.
        
        Args:
            baseline_dir: Directory with baseline screenshots
            current_dir: Directory with current screenshots
            diff_dir: Directory to save diff images (default: current_dir / "diffs")
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for visual comparison. Install with: pip install pillow")
        
        self.baseline_dir = Path(baseline_dir)
        self.current_dir = Path(current_dir)
        self.diff_dir = Path(diff_dir) if diff_dir else self.current_dir / "diffs"
        self.diff_dir.mkdir(parents=True, exist_ok=True)
        
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.current_dir.mkdir(parents=True, exist_ok=True)
    
    def compare_screenshot(
        self, 
        screenshot_name: str, 
        threshold: float = 0.01,
        update_baseline: bool = False
    ) -> Dict[str, Any]:
        """
        Compare a screenshot with baseline.
        
        Args:
            screenshot_name: Name of screenshot file
            threshold: Difference threshold (0.0 to 1.0, default: 0.01 = 1%)
            update_baseline: If True, update baseline instead of comparing
        
        Returns:
            Dict with comparison results:
            - match: bool - Whether screenshots match
            - difference: float - Difference percentage (0.0 to 1.0)
            - diff_path: Optional[Path] - Path to diff image if different
            - baseline_path: Path - Path to baseline screenshot
            - current_path: Path - Path to current screenshot
        """
        baseline_path = self.baseline_dir / screenshot_name
        current_path = self.current_dir / screenshot_name
        
        # Ensure screenshot has extension
        if not screenshot_name.endswith(('.png', '.jpeg', '.jpg')):
            baseline_path = self.baseline_dir / f"{screenshot_name}.png"
            current_path = self.current_dir / f"{screenshot_name}.png"
        
        # If updating baseline, copy current to baseline
        if update_baseline:
            if current_path.exists():
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(current_path, baseline_path)
                logger.info(f"Baseline updated: {baseline_path}")
                return {
                    'match': True,
                    'difference': 0.0,
                    'diff_path': None,
                    'baseline_path': baseline_path,
                    'current_path': current_path,
                    'updated': True
                }
            else:
                return {
                    'match': False,
                    'difference': 1.0,
                    'error': f"Current screenshot not found: {current_path}",
                    'baseline_path': baseline_path,
                    'current_path': current_path
                }
        
        # If baseline doesn't exist, create it from current
        if not baseline_path.exists():
            if current_path.exists():
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(current_path, baseline_path)
                logger.info(f"Baseline created from current: {baseline_path}")
                return {
                    'match': True,
                    'difference': 0.0,
                    'diff_path': None,
                    'baseline_path': baseline_path,
                    'current_path': current_path,
                    'created': True
                }
            else:
                return {
                    'match': False,
                    'difference': 1.0,
                    'error': f"Neither baseline nor current screenshot found: {baseline_path}",
                    'baseline_path': baseline_path,
                    'current_path': current_path
                }
        
        # If current doesn't exist, it's a failure
        if not current_path.exists():
            return {
                'match': False,
                'difference': 1.0,
                'error': f"Current screenshot not found: {current_path}",
                'baseline_path': baseline_path,
                'current_path': current_path
            }
        
        # Compare images
        try:
            baseline_img = Image.open(baseline_path)
            current_img = Image.open(current_path)
            
            # Ensure same size
            if baseline_img.size != current_img.size:
                # Resize current to match baseline
                current_img = current_img.resize(baseline_img.size, Image.Resampling.LANCZOS)
                logger.warning(f"Screenshot size mismatch: baseline {baseline_img.size}, current {current_img.size}. Resized current.")
            
            # Convert to RGB if needed
            if baseline_img.mode != 'RGB':
                baseline_img = baseline_img.convert('RGB')
            if current_img.mode != 'RGB':
                current_img = current_img.convert('RGB')
            
            # Calculate difference
            diff = ImageChops.difference(baseline_img, current_img)
            
            # Calculate difference percentage
            diff_pixels = diff.getbbox()
            if diff_pixels:
                # Count different pixels
                diff_data = diff.getdata()
                total_pixels = baseline_img.size[0] * baseline_img.size[1]
                different_pixels = sum(1 for pixel in diff_data if sum(pixel) > 0)
                difference_ratio = different_pixels / total_pixels
            else:
                difference_ratio = 0.0
            
            match = difference_ratio <= threshold
            
            # Create diff image if different
            diff_path = None
            if not match:
                diff_path = self._create_diff_image(
                    baseline_img, 
                    current_img, 
                    diff, 
                    screenshot_name,
                    difference_ratio
                )
            
            return {
                'match': match,
                'difference': difference_ratio,
                'diff_path': diff_path,
                'baseline_path': baseline_path,
                'current_path': current_path,
                'threshold': threshold
            }
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {e}")
            return {
                'match': False,
                'difference': 1.0,
                'error': str(e),
                'baseline_path': baseline_path,
                'current_path': current_path
            }
    
    def _create_diff_image(
        self, 
        baseline: Image.Image, 
        current: Image.Image, 
        diff: Image.Image,
        screenshot_name: str,
        difference_ratio: float
    ) -> Path:
        """Create a side-by-side diff image."""
        # Create a composite image showing baseline, current, and diff
        width, height = baseline.size
        
        # Create canvas for side-by-side comparison
        canvas_width = width * 3 + 40  # 3 images + spacing
        canvas_height = height + 60  # Image + header
        
        canvas = Image.new('RGB', (canvas_width, canvas_height), color='white')
        draw = ImageDraw.Draw(canvas)
        
        # Try to load font, fallback to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Draw labels
        if font:
            draw.text((10, 10), "Baseline", fill='black', font=font)
            draw.text((width + 20, 10), "Current", fill='black', font=font)
            draw.text((width * 2 + 30, 10), f"Diff ({difference_ratio*100:.2f}%)", fill='red', font=font)
        
        # Paste images
        canvas.paste(baseline, (10, 40))
        canvas.paste(current, (width + 20, 40))
        
        # Enhance diff for visibility
        diff_enhanced = diff.convert('RGB')
        # Make differences more visible
        diff_pixels = diff_enhanced.load()
        for y in range(diff_enhanced.size[1]):
            for x in range(diff_enhanced.size[0]):
                r, g, b = diff_pixels[x, y]
                if r > 0 or g > 0 or b > 0:
                    # Highlight differences in red
                    diff_pixels[x, y] = (255, 0, 0)
        
        canvas.paste(diff_enhanced, (width * 2 + 30, 40))
        
        # Save diff image
        diff_filename = f"diff_{screenshot_name}"
        if not diff_filename.endswith('.png'):
            diff_filename = f"{diff_filename}.png"
        
        diff_path = self.diff_dir / diff_filename
        canvas.save(diff_path)
        
        logger.info(f"Diff image saved: {diff_path} (difference: {difference_ratio*100:.2f}%)")
        
        return diff_path
    
    def compare_all_screenshots(
        self, 
        threshold: float = 0.01,
        update_baseline: bool = False
    ) -> Dict[str, Any]:
        """
        Compare all screenshots in current directory with baseline.
        
        Args:
            threshold: Difference threshold
            update_baseline: If True, update all baselines
        
        Returns:
            Dict with results for each screenshot
        """
        results = {}
        
        # Get all screenshots from current directory
        screenshot_files = list(self.current_dir.glob("*.png")) + list(self.current_dir.glob("*.jpg")) + list(self.current_dir.glob("*.jpeg"))
        
        for screenshot_path in screenshot_files:
            screenshot_name = screenshot_path.name
            result = self.compare_screenshot(screenshot_name, threshold, update_baseline)
            results[screenshot_name] = result
        
        # Summary
        total = len(results)
        matches = sum(1 for r in results.values() if r.get('match', False))
        differences = total - matches
        
        return {
            'results': results,
            'summary': {
                'total': total,
                'matches': matches,
                'differences': differences,
                'threshold': threshold
            }
        }

