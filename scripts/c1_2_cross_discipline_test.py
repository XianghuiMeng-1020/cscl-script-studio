#!/usr/bin/env python3
"""Cross-discipline end-to-end test for C1-2"""
import os
import sys
import json
import requests
from datetime import datetime

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')

# Test specs for 3 disciplines
DISCIPLINES = {
    'data_science': {
        'name': 'Data Science',
        'spec': {
            'course_context': {
                'subject': 'Data Science',
                'topic': 'Machine Learning Ethics',
                'class_size': 30,
                'mode': 'sync',
                'duration': 90
            },
            'learning_objectives': {
                'knowledge': ['Understand ML ethics principles', 'Know bias detection methods'],
                'skills': ['Analyze ethical implications', 'Design fair algorithms']
            },
            'task_requirements': {
                'task_type': 'debate',
                'expected_output': 'argument for/against ML in healthcare',
                'collaboration_form': 'group'
            }
        }
    },
    'learning_sciences': {
        'name': 'Learning Sciences',
        'spec': {
            'course_context': {
                'subject': 'Learning Sciences',
                'topic': 'Collaborative Learning Strategies',
                'class_size': 25,
                'mode': 'async',
                'duration': 120
            },
            'learning_objectives': {
                'knowledge': ['Understand collaboration principles', 'Know scaffolding techniques'],
                'skills': ['Facilitate group discussions', 'Design collaborative activities']
            },
            'task_requirements': {
                'task_type': 'collaborative_writing',
                'expected_output': 'group essay on collaboration',
                'collaboration_form': 'pair'
            }
        }
    },
    'humanities': {
        'name': 'Humanities',
        'spec': {
            'course_context': {
                'subject': 'Humanities',
                'topic': 'Literary Analysis Methods',
                'class_size': 20,
                'mode': 'sync',
                'duration': 60
            },
            'learning_objectives': {
                'knowledge': ['Understand literary devices', 'Know analysis frameworks'],
                'skills': ['Analyze texts', 'Write critiques']
            },
            'task_requirements': {
                'task_type': 'peer_review',
                'expected_output': 'peer feedback on analysis',
                'collaboration_form': 'pair'
            }
        }
    }
}


def login_teacher():
    """Login as teacher and return session"""
    resp = requests.post(
        f'{BASE_URL}/api/auth/login',
        json={'user_id': 'T001', 'password': 'teacher123'}
    )
    if resp.status_code != 200:
        print(f"Login failed: {resp.status_code}")
        return None
    return resp.cookies


def create_script(cookies, discipline_name, topic, task_type, duration):
    """Create a script"""
    resp = requests.post(
        f'{BASE_URL}/api/cscl/scripts',
        json={
            'title': f'{discipline_name} Script',
            'topic': topic,
            'task_type': task_type,
            'duration_minutes': duration
        },
        cookies=cookies
    )
    if resp.status_code != 201:
        print(f"Create script failed: {resp.status_code} - {resp.text}")
        return None
    return json.loads(resp.text)['script']['id']


def validate_spec(spec):
    """Validate spec"""
    resp = requests.post(
        f'{BASE_URL}/api/cscl/spec/validate',
        json=spec
    )
    return resp.status_code == 200, json.loads(resp.text) if resp.status_code == 200 else None


def run_pipeline(cookies, script_id, spec):
    """Run pipeline"""
    resp = requests.post(
        f'{BASE_URL}/api/cscl/scripts/{script_id}/pipeline/run',
        json={'spec': spec, 'generation_options': {}},
        cookies=cookies
    )
    return resp.status_code, json.loads(resp.text) if resp.status_code == 200 else json.loads(resp.text) if resp.text else {}


def get_run_details(cookies, run_id):
    """Get run details"""
    resp = requests.get(
        f'{BASE_URL}/api/cscl/pipeline/runs/{run_id}',
        cookies=cookies
    )
    if resp.status_code != 200:
        return None
    return json.loads(resp.text)


def main():
    """Run cross-discipline tests"""
    print("=== C1-2 Cross-Discipline End-to-End Test ===\n")
    
    cookies = login_teacher()
    if not cookies:
        print("Failed to login. Make sure server is running and T001 user exists.")
        sys.exit(1)
    
    results = {}
    
    for discipline_key, discipline_data in DISCIPLINES.items():
        print(f"\n--- Testing {discipline_data['name']} ---")
        
        spec = discipline_data['spec']
        
        # 1. Validate spec
        print("1. Validating spec...")
        valid, validation_result = validate_spec(spec)
        if not valid:
            print(f"   ❌ Spec validation failed: {validation_result}")
            results[discipline_key] = {'status': 'failed', 'step': 'validation'}
            continue
        print("   ✅ Spec validated")
        
        # 2. Create script
        print("2. Creating script...")
        script_id = create_script(
            cookies,
            discipline_data['name'],
            spec['course_context']['topic'],
            spec['task_requirements']['task_type'],
            spec['course_context']['duration']
        )
        if not script_id:
            results[discipline_key] = {'status': 'failed', 'step': 'create_script'}
            continue
        print(f"   ✅ Script created: {script_id}")
        
        # 3. Run pipeline
        print("3. Running pipeline...")
        status_code, pipeline_result = run_pipeline(cookies, script_id, spec)
        if status_code != 200:
            print(f"   ❌ Pipeline failed: {status_code} - {pipeline_result.get('error', 'Unknown')}")
            results[discipline_key] = {
                'status': 'failed',
                'step': 'pipeline',
                'error': pipeline_result.get('error'),
                'script_id': script_id
            }
            continue
        
        run_id = pipeline_result.get('run_id')
        print(f"   ✅ Pipeline completed: {run_id}")
        
        # 4. Get run details
        print("4. Getting run details...")
        run_details = get_run_details(cookies, run_id)
        if not run_details:
            print("   ⚠️  Could not get run details")
        else:
            print(f"   ✅ Run details retrieved: {len(run_details.get('stages', []))} stages")
        
        # 5. Extract quality metrics
        quality_report = pipeline_result.get('quality_report', {})
        coverage = quality_report.get('coverage', {})
        pedagogical = quality_report.get('pedagogical_alignment', {})
        
        results[discipline_key] = {
            'status': 'success',
            'run_id': run_id,
            'script_id': script_id,
            'quality': {
                'coverage': {
                    'required_fields': coverage.get('required_fields_coverage', 0),
                    'scene_completeness': coverage.get('scene_completeness', 0),
                    'role_completeness': coverage.get('role_completeness', 0)
                },
                'pedagogical_alignment': {
                    'objective_alignment': pedagogical.get('objective_alignment_score', 0),
                    'task_fit': pedagogical.get('task_fit_score', 0)
                }
            },
            'stages_count': len(pipeline_result.get('stages', []))
        }
        
        print(f"   Quality: coverage={coverage.get('required_fields_coverage', 0):.2f}, "
              f"scene={coverage.get('scene_completeness', 0):.2f}, "
              f"role={coverage.get('role_completeness', 0):.2f}")
    
    # Export results
    output_file = f'outputs/c1_2/cross_discipline_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    os.makedirs('outputs/c1_2', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'disciplines': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Results exported to {output_file} ===")
    print("\nSummary:")
    for key, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} {DISCIPLINES[key]['name']}: {result.get('run_id', 'N/A')}")
    
    return results


if __name__ == '__main__':
    main()
