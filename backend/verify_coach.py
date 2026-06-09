import sys
import os
from app import create_app
from extensions import db, ctx
from models.distributor import Distributor
from services.ai_coach_service import ai_coach_service
from skills.coach import CoachSkill

def test_coach_logic():
    print("Initializing Flask App context...")
    app = create_app()
    with app.app_context():
        db.session.rollback()
        
        # Find or create a test distributor
        dist = Distributor.query.filter_by(email="test_coach@enpi.ai").first()
        if not dist:
            print("Creating test distributor...")
            dist = Distributor(
                name="Distribuidor Test Coach",
                email="test_coach@enpi.ai",
                herbalife_level="Supervisor",
                coach_mode_enabled=True,
                coach_music_preference="spanish"
            )
            db.session.add(dist)
            db.session.commit()
            
        print(f"Distributor: {dist.name}, Level: {dist.herbalife_level}")
        
        # Test 1: Level metadata
        meta = ai_coach_service.get_level_metadata(dist.herbalife_level)
        print(f"Level Progress: {meta['progress']}%")
        print(f"Level Tasks: {meta['tasks']}")
        
        # Test 2: Initial tasks status
        tasks_checklist = ai_coach_service.generate_daily_tasks_checklist(dist.herbalife_level)
        print(f"Checklist Template: {tasks_checklist}")
        dist.coach_daily_tasks_status = tasks_checklist
        db.session.commit()
        
        # Test 3: Generate messages
        morning_msg = ai_coach_service.generate_daily_coach_message(
            distributor_name=dist.name,
            language="es",
            level=dist.herbalife_level,
            tasks_status=dist.coach_daily_tasks_status
        )
        print("\n--- MORNING MESSAGE ---")
        print(morning_msg)
        
        midday_msg = ai_coach_service.generate_midday_coach_message(
            distributor_name=dist.name,
            language="es",
            level=dist.herbalife_level,
            country="Ecuador"
        )
        print("\n--- MIDDAY MESSAGE ---")
        print(midday_msg)
        
        evening_msg = ai_coach_service.generate_evening_coach_message(
            distributor_name=dist.name,
            language="es",
            level=dist.herbalife_level,
            tasks_status=dist.coach_daily_tasks_status
        )
        print("\n--- EVENING MESSAGE ---")
        print(evening_msg)
        
        # Test 4: Roadmap Researcher agent
        print("\nRunning Roadmap Researcher Agent...")
        research_results = ai_coach_service.run_roadmap_research(dist.id)
        print("Researcher Results:")
        print(research_results)
        
        # Test 5: Skill execution
        print("\nTesting Coach Skill tools...")
        from flask import g
        ctx.current_company = dist
        skill = CoachSkill()
        
        # Test get_coach_roadmap tool
        roadmap_str = skill.get_coach_roadmap()
        print("Roadmap String:")
        print(roadmap_str)
        
        # Test update_coach_tasks_status tool
        update_res = skill.update_coach_tasks_status("take_product", True)
        print(f"Update Result: {update_res}")
        
        # Clean up test data
        from services.cron_service import ScheduledTask
        ScheduledTask.query.filter_by(distributor_id=dist.id).delete()
        db.session.delete(dist)
        db.session.commit()
        print("\nAll Coach Mode tests passed successfully!")

if __name__ == "__main__":
    test_coach_logic()
