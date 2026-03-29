"""Image generation service - integrates OpenAI DALL-E for creating educational visuals"""
import os
import base64
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

from app.config import Config
from app.db import db

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating educational images using OpenAI DALL-E"""
    
    def __init__(self):
        self.enabled = getattr(Config, 'IMAGE_GENERATION_ENABLED', False)
        self.api_key = getattr(Config, 'OPENAI_API_KEY', '')
        self.model = getattr(Config, 'OPENAI_IMAGE_MODEL', 'dall-e-3')
        self.base_url = getattr(Config, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.image_dir = os.path.join(Config.DATA_DIR, 'generated_images')
        
        # Ensure image directory exists
        os.makedirs(self.image_dir, exist_ok=True)
    
    def is_enabled(self) -> bool:
        """Check if image generation is enabled and configured"""
        return self.enabled and bool(self.api_key)
    
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        script_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an image using DALL-E
        
        Args:
            prompt: The image generation prompt
            size: Image size (1024x1024, 1024x1792, 1792x1024)
            quality: Image quality (standard, hd)
            style: Image style (vivid, natural)
            script_id: Associated script/activity ID
            metadata: Additional metadata about the image
        
        Returns:
            Dict with success status, image data, and metadata
        """
        if not self.is_enabled():
            return {
                'success': False,
                'error': 'Image generation is not enabled or not configured'
            }
        
        try:
            # Prepare the API request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'prompt': prompt,
                'size': size,
                'quality': quality,
                'style': style,
                'response_format': 'b64_json',
                'n': 1
            }
            
            # Make the API request
            response = requests.post(
                f'{self.base_url}/images/generations',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if not response.ok:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'API request failed: {response.status_code}')
                logger.error(f"Image generation failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            data = response.json()
            image_data = data['data'][0]['b64_json']
            revised_prompt = data['data'][0].get('revised_prompt', prompt)
            
            # Generate unique filename
            image_id = str(uuid.uuid4())
            filename = f"{image_id}.png"
            filepath = os.path.join(self.image_dir, filename)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(image_data))
            
            # Create metadata record
            image_record = {
                'id': image_id,
                'script_id': script_id,
                'original_prompt': prompt,
                'revised_prompt': revised_prompt,
                'filename': filename,
                'filepath': filepath,
                'size': size,
                'quality': quality,
                'style': style,
                'model': self.model,
                'metadata': metadata or {},
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Save metadata to JSON file
            self._save_image_metadata(image_record)
            
            logger.info(f"Image generated successfully: {filename} for script {script_id}")
            
            return {
                'success': True,
                'image_id': image_id,
                'filename': filename,
                'filepath': filepath,
                'revised_prompt': revised_prompt,
                'metadata': image_record
            }
            
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_instructional_visuals(
        self,
        spec: Dict[str, Any],
        planner_output: Dict[str, Any],
        script_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate instructional visuals based on activity specification
        
        This creates images for:
        - Student slides visual support (title slides, task steps, process diagrams)
        - Worksheet examples and task materials
        - Visual scaffolds for group work
        
        Args:
            spec: Activity specification
            planner_output: Output from planner stage
            script_id: Associated script ID
        
        Returns:
            List of generated image records
        """
        if not self.is_enabled():
            return []
        
        generated_images = []
        topic = spec.get('topic', 'Learning Activity')
        task_type = spec.get('task_type', 'general')
        
        # Define image generation scenarios based on task type
        generation_tasks = self._get_visual_tasks(spec, planner_output)
        
        for task in generation_tasks:
            try:
                result = self.generate_image(
                    prompt=task['prompt'],
                    size=task.get('size', '1024x1024'),
                    quality=task.get('quality', 'standard'),
                    style=task.get('style', 'vivid'),
                    script_id=script_id,
                    metadata={
                        'purpose': task['purpose'],
                        'target': task.get('target', 'general'),
                        'topic': topic,
                        'task_type': task_type
                    }
                )
                
                if result['success']:
                    generated_images.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to generate {task['purpose']}: {str(e)}")
                continue
        
        return generated_images
    
    def _get_visual_tasks(self, spec: Dict[str, Any], planner_output: Dict[str, Any]) -> List[Dict[str, str]]:
        """Determine what visuals to generate based on activity type"""
        topic = spec.get('topic', 'Learning Activity')
        task_type = spec.get('task_type', 'general')
        learning_objectives = spec.get('learning_objectives', [])
        
        tasks = []
        
        # Task 1: Activity title/introduction visual
        tasks.append({
            'purpose': 'activity_intro',
            'prompt': f"Create a clean, educational title slide visual for a group learning activity about '{topic}'. "
                      f"Include subtle visual elements representing collaboration and learning. "
                      f"Style: minimalist, professional, suitable for classroom presentation. "
                      f"No text, only visual elements.",
            'size': '1024x1024',
            'target': 'student_slides'
        })
        
        # Task 2: Process/task flow diagram (if collaborative activity)
        if task_type in ['jigsaw', 'peer_review', 'structured_debate', 'collaborative_inquiry']:
            tasks.append({
                'purpose': 'process_diagram',
                'prompt': f"Create a simple process flow diagram showing steps for a collaborative '{task_type}' activity about '{topic}'. "
                          f"Show group stages: individual work, group sharing, synthesis, presentation. "
                          f"Use icons and arrows, clean educational style, no text labels. "
                          f"Colors: soft blues and greens, professional classroom aesthetic.",
                'size': '1024x1024',
                'target': 'student_slides'
            })
        
        # Task 3: Data visualization example (if data interpretation task)
        if any(keyword in str(learning_objectives).lower() for keyword in ['data', 'chart', 'graph', 'visualization', 'analyze']):
            tasks.append({
                'purpose': 'data_visualization_example',
                'prompt': f"Create a clean, educational chart or diagram about '{topic}'. "
                          f"Simple bar chart or line graph style, easy to read, professional look. "
                          f"Use appropriate colors, include grid lines, axis labels (if needed). "
                          f"Style: clear, educational, suitable for student analysis exercise.",
                'size': '1024x1024',
                'target': 'worksheet'
            })
            
            # Add a "good vs poor" comparison for critique activities
            if 'critique' in str(learning_objectives).lower() or task_type == 'chart_critique':
                tasks.append({
                    'purpose': 'chart_comparison_good',
                    'prompt': f"Create a well-designed, clear data visualization about '{topic}'. "
                              f"Good practices: clear labels, appropriate scale, consistent colors, proper legend. "
                              f"Style: professional, educational, exemplary chart for teaching.",
                    'size': '1024x1024',
                    'target': 'worksheet'
                })
                
                tasks.append({
                    'purpose': 'chart_comparison_poor',
                    'prompt': f"Create a poorly designed, confusing data visualization about '{topic}' with intentional design flaws. "
                              f"Include problems: inconsistent colors, misleading scale, cluttered labels, 3D distortion. "
                              f"Style: busy, unclear, as an example of what NOT to do for student critique exercise.",
                    'size': '1024x1024',
                    'target': 'worksheet'
                })
        
        # Task 4: Group roles visualization (for collaborative activities)
        if task_type in ['jigsaw', 'collaborative_inquiry', 'peer_review']:
            tasks.append({
                'purpose': 'group_roles',
                'prompt': f"Create a simple infographic showing different roles in a collaborative group for '{topic}' learning. "
                          f"Show 3-4 distinct role icons: facilitator, recorder, timekeeper, presenter. "
                          f"Style: clean, modern, icon-based, suitable for student handout. "
                          f"Soft colors, clear visual hierarchy.",
                'size': '1024x1024',
                'target': 'worksheet'
            })
        
        # Task 5: Facilitation timeline (for teacher)
        tasks.append({
                'purpose': 'facilitation_timeline',
                'prompt': f"Create a visual timeline diagram for facilitating a '{topic}' group activity. "
                          f"Show phases: introduction (5min), group work (15-20min), synthesis (10min), debrief (10min). "
                          f"Simple horizontal timeline with phase blocks, clean educational style. "
                          f"Colors: soft greens and blues, professional teacher reference card aesthetic.",
                'size': '1792x1024',
                'target': 'teacher_facilitation'
            })
        
        return tasks
    
    def _save_image_metadata(self, record: Dict[str, Any]):
        """Save image metadata to JSON file"""
        metadata_file = os.path.join(self.image_dir, 'image_metadata.json')
        
        try:
            # Load existing metadata
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    import json
                    data = json.load(f)
            else:
                data = {'images': []}
            
            # Add new record
            data['images'].append(record)
            
            # Save back
            with open(metadata_file, 'w') as f:
                import json
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save image metadata: {str(e)}")
    
    def get_images_for_script(self, script_id: str) -> List[Dict[str, Any]]:
        """Get all generated images for a specific script/activity"""
        metadata_file = os.path.join(self.image_dir, 'image_metadata.json')
        
        if not os.path.exists(metadata_file):
            return []
        
        try:
            import json
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            return [
                img for img in data.get('images', [])
                if img.get('script_id') == script_id
            ]
        except Exception as e:
            logger.error(f"Failed to load image metadata: {str(e)}")
            return []
    
    def get_image_url(self, image_id: str) -> Optional[str]:
        """Get the URL/path for a generated image"""
        metadata_file = os.path.join(self.image_dir, 'image_metadata.json')
        
        if not os.path.exists(metadata_file):
            return None
        
        try:
            import json
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            for img in data.get('images', []):
                if img.get('id') == image_id:
                    return f'/generated_images/{img.get("filename")}'
            
            return None
        except Exception as e:
            logger.error(f"Failed to get image URL: {str(e)}")
            return None


# Singleton instance
_image_service = None

def get_image_generation_service() -> ImageGenerationService:
    """Get or create the image generation service singleton"""
    global _image_service
    if _image_service is None:
        _image_service = ImageGenerationService()
    return _image_service