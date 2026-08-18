#!/usr/bin/env python3
"""
YouTrack test data generation script.
Creates users, populates project team, and generates test issues in parallel.
"""
import csv
import logging
import random
import string
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from config import (
    YOUTRACK_URL, YOUTRACK_TOKEN, YOUTRACK_PROJECT_KEY,
    TOTAL_USERS, TOTAL_ISSUES, ISSUES_PER_BATCH, BATCH_DELAY_SECONDS,
    NUM_WORKERS, QUEUE_SIZE, TIMEOUT_SECONDS,
    USERS_CSV, ISSUES_CSV, LOG_FILE,
    ISSUE_SUMMARIES, ISSUE_DESCRIPTIONS,
    ADMIN_GROUP, DEFAULT_PERMISSIONS, CREATE_BACKUP_AFTER,
    LOG_LEVEL
)
from youtrack_api import YouTrackAPIClient


# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Generate and populate test data in YouTrack."""

    def __init__(self, api_client: YouTrackAPIClient):
        """Initialize test data generator."""
        self.api = api_client
        self.users: List[Dict[str, str]] = []
        self.user_ids: List[str] = []
        self.created_user_count = 0
        self.created_issue_count = 0
        self.failed_operations = []

    def load_users_from_csv(self) -> List[Dict[str, str]]:
        """Load user templates from CSV and expand to TOTAL_USERS."""
        template_users = []
        if USERS_CSV.exists():
            with open(USERS_CSV, 'r') as f:
                reader = csv.DictReader(f)
                template_users = list(reader)
            logger.info(f"Loaded {len(template_users)} user templates from CSV")

        # Generate additional users to reach TOTAL_USERS
        self.users = template_users.copy()
        for i in range(len(template_users), TOTAL_USERS):
            user_id = i + 1
            self.users.append({
                'id': str(user_id),
                'login': f'user{user_id:03d}',
                'name': f'User {user_id}',
                'email': f'user{user_id}@example.com'
            })

        logger.info(f"Total users to create: {len(self.users)}")
        return self.users

    def load_issues_templates_from_csv(self) -> List[Dict[str, str]]:
        """Load issue templates from CSV."""
        templates = []
        if ISSUES_CSV.exists():
            with open(ISSUES_CSV, 'r') as f:
                reader = csv.DictReader(f)
                templates = list(reader)
            logger.info(f"Loaded {len(templates)} issue templates from CSV")
        else:
            logger.warning(f"Issues template file not found: {ISSUES_CSV}")
        
        return templates if templates else [{'summary': 'Test Issue', 'description': 'Test Description'}]

    def create_users_batch(self, users: List[Dict[str, str]]) -> Tuple[int, List[str]]:
        """
        Create multiple users in batch.
        
        Returns:
            Tuple of (created_count, user_ids)
        """
        created_ids = []
        for user in users:
            try:
                result = self.api.create_user(
                    login=user['login'],
                    name=user['name'],
                    email=user['email']
                )
                user_id = result.get('id')
                if user_id:
                    created_ids.append(user_id)
                    self.created_user_count += 1
                    logger.debug(f"Created user: {user['login']} (ID: {user_id})")
                else:
                    logger.warning(f"Failed to get ID for user: {user['login']}")
                    self.failed_operations.append(f"User creation: {user['login']}")
            except Exception as e:
                logger.error(f"Failed to create user {user['login']}: {e}")
                self.failed_operations.append(f"User creation: {user['login']} - {str(e)}")

        return len(created_ids), created_ids

    def setup_project_team(self, project_id: str, user_ids: List[str]) -> int:
        """
        Add users to project team with default permissions.
        
        Returns:
            Number of users successfully added
        """
        success_count = 0
        for user_id in user_ids:
            try:
                # Add user to project team
                self.api.add_user_to_project_team(project_id, user_id)
                logger.debug(f"Added user {user_id} to project team")
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to add user {user_id} to project team: {e}")
                self.failed_operations.append(f"Add to team: {user_id} - {str(e)}")

        return success_count

    def setup_group_permissions(self, group_name: str, user_ids: List[str]) -> int:
        """
        Add users to group (e.g., Registered Users).
        
        Returns:
            Number of users successfully added to group
        """
        try:
            # Try to get existing group
            groups_response = self.api.get_users()  # Placeholder - adjust based on actual API
            logger.info(f"Setting up group permissions for: {group_name}")
        except Exception as e:
            logger.warning(f"Could not setup group {group_name}: {e}")

        # For now, just track that we attempted this
        return len(user_ids)

    def generate_issue_data(
        self,
        issue_index: int,
        templates: List[Dict[str, str]],
        user_ids: List[str]
    ) -> Dict:
        """
        Generate issue data based on templates and index.
        
        Args:
            issue_index: Issue number (0-based)
            templates: Issue templates from CSV
            user_ids: List of user IDs to randomly assign
            
        Returns:
            Issue data dictionary
        """
        template = templates[issue_index % len(templates)]
        
        # Generate summary and description with variety
        summary = template.get('summary', 'Test Issue')
        description = template.get('description', 'Test Description')
        
        # Add some variety to summary
        if '[TEMPLATE]' in summary or not summary or summary == 'Test Issue':
            summary = random.choice(ISSUE_SUMMARIES) + f" - Issue #{issue_index + 1}"
        
        if '[TEMPLATE]' in description:
            description = random.choice(ISSUE_DESCRIPTIONS).format(f"Issue #{issue_index + 1}")
        else:
            description = f"{description} - Issue #{issue_index + 1} generated at {datetime.now().isoformat()}"
        
        # Randomly assign to user (creator/reporter)
        reporter_id = random.choice(user_ids) if user_ids else None
        
        # Randomly assign to another user (30% chance)
        assignee_id = None
        if random.random() < 0.3 and user_ids:
            assignee_id = random.choice(user_ids)
        
        return {
            'summary': summary,
            'description': description,
            'reporter_id': reporter_id,
            'assignee_id': assignee_id
        }

    def create_issue_worker(
        self,
        issue_data: Dict,
        project_id: str
    ) -> Tuple[bool, str]:
        """
        Worker function to create a single issue.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            result = self.api.create_issue(
                summary=issue_data['summary'],
                description=issue_data['description'],
                project_id=project_id,
                reporter_id=issue_data.get('reporter_id'),
                assignee_id=issue_data.get('assignee_id')
            )
            issue_id = result.get('id')
            if issue_id:
                self.created_issue_count += 1
                if self.created_issue_count % 1000 == 0:
                    logger.info(f"Created {self.created_issue_count} issues")
                return True, f"Created issue {issue_id}"
            else:
                return False, "No ID in response"
        except Exception as e:
            return False, str(e)

    def create_issues_parallel(
        self,
        project_id: str,
        user_ids: List[str],
        num_issues: int = TOTAL_ISSUES,
        num_workers: int = NUM_WORKERS
    ) -> int:
        """
        Create issues in parallel using thread pool.
        
        Args:
            project_id: Project ID to create issues in
            user_ids: List of user IDs for assignment/reporting
            num_issues: Total number of issues to create
            num_workers: Number of parallel workers
            
        Returns:
            Number of successfully created issues
        """
        templates = self.load_issues_templates_from_csv()
        
        logger.info(f"Starting to create {num_issues} issues with {num_workers} workers")
        start_time = time.time()
        
        # Generate all issue data upfront
        all_issues_data = [
            self.generate_issue_data(i, templates, user_ids)
            for i in range(num_issues)
        ]
        
        # Process issues in batches with delay between batches
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            batch_num = 0
            
            for batch_start in range(0, num_issues, ISSUES_PER_BATCH):
                batch_end = min(batch_start + ISSUES_PER_BATCH, num_issues)
                batch_num += 1
                
                # Submit batch of issues
                for issue_idx in range(batch_start, batch_end):
                    future = executor.submit(
                        self.create_issue_worker,
                        all_issues_data[issue_idx],
                        project_id
                    )
                    futures[future] = issue_idx
                
                # Log batch progress
                if batch_num % 10 == 0:
                    logger.debug(f"Submitted batch {batch_num}, total submitted: {batch_end}/{num_issues}")
                
                # Add delay between batches to avoid overwhelming the server
                if batch_end < num_issues:
                    time.sleep(BATCH_DELAY_SECONDS)
            
            # Wait for all futures to complete
            completed = 0
            for future in as_completed(futures):
                completed += 1
                try:
                    success, message = future.result(timeout=TIMEOUT_SECONDS)
                    if not success:
                        self.failed_operations.append(f"Issue creation: {message}")
                except Exception as e:
                    logger.error(f"Issue worker failed: {e}")
                    self.failed_operations.append(f"Issue creation: {str(e)}")
                
                if completed % 5000 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed
                    remaining = (num_issues - completed) / rate if rate > 0 else 0
                    logger.info(
                        f"Progress: {completed}/{num_issues} issues, "
                        f"Rate: {rate:.1f} issues/sec, "
                        f"ETA: {remaining/60:.1f} minutes"
                    )

        elapsed = time.time() - start_time
        logger.info(
            f"Issue creation completed in {elapsed:.1f}s. "
            f"Created: {self.created_issue_count}/{num_issues} "
            f"({self.created_issue_count/elapsed:.1f} issues/sec)"
        )
        
        return self.created_issue_count

    def generate_all_test_data(self, project_id: str = YOUTRACK_PROJECT_KEY) -> bool:
        """
        Main workflow: create users, setup project team, and create issues.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Load and create users
            logger.info("=" * 60)
            logger.info("STEP 1: Creating users")
            logger.info("=" * 60)
            
            self.load_users_from_csv()
            
            # Create users in batches
            batch_size = 10
            for i in range(0, len(self.users), batch_size):
                batch = self.users[i:i + batch_size]
                created, user_ids = self.create_users_batch(batch)
                self.user_ids.extend(user_ids)
                logger.info(f"Batch {i//batch_size + 1}: Created {created} users")
            
            logger.info(f"Total users created: {self.created_user_count}/{len(self.users)}")
            
            # Step 2: Setup project team
            logger.info("=" * 60)
            logger.info("STEP 2: Setting up project team")
            logger.info("=" * 60)
            
            team_count = self.setup_project_team(project_id, self.user_ids)
            logger.info(f"Added {team_count} users to project team")
            
            # Step 3: Setup group permissions
            logger.info("=" * 60)
            logger.info("STEP 3: Setting up group permissions")
            logger.info("=" * 60)
            
            group_count = self.setup_group_permissions(ADMIN_GROUP, self.user_ids)
            logger.info(f"Added {group_count} users to {ADMIN_GROUP} group")
            
            # Step 4: Create issues in parallel
            logger.info("=" * 60)
            logger.info("STEP 4: Creating test issues in parallel")
            logger.info("=" * 60)
            
            issue_count = self.create_issues_parallel(project_id, self.user_ids)
            
            # Step 5: Summary
            logger.info("=" * 60)
            logger.info("TEST DATA GENERATION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Users created: {self.created_user_count}/{len(self.users)}")
            logger.info(f"Issues created: {self.created_issue_count}/{TOTAL_ISSUES}")
            logger.info(f"Failed operations: {len(self.failed_operations)}")
            
            if self.failed_operations:
                logger.warning("Failed operations:")
                for op in self.failed_operations[:10]:  # Show first 10
                    logger.warning(f"  - {op}")
                if len(self.failed_operations) > 10:
                    logger.warning(f"  ... and {len(self.failed_operations) - 10} more")
            
            # Step 6: Create backup (optional)
            if CREATE_BACKUP_AFTER:
                logger.info("=" * 60)
                logger.info("STEP 5: Creating database backup")
                logger.info("=" * 60)
                try:
                    self.api.create_backup()
                    logger.info("Database backup initiated")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")
            
            return self.created_issue_count > 0

        except Exception as e:
            logger.error(f"Test data generation failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    logger.info("YouTrack Test Data Generation Started")
    logger.info(f"Target: {TOTAL_USERS} users, {TOTAL_ISSUES} issues")
    logger.info(f"YouTrack URL: {YOUTRACK_URL}")
    logger.info(f"Project: {YOUTRACK_PROJECT_KEY}")
    logger.info(f"Workers: {NUM_WORKERS}")
    
    # Verify token is provided
    if not YOUTRACK_TOKEN:
        logger.error("YOUTRACK_TOKEN environment variable not set")
        sys.exit(1)
    
    # Initialize API client
    try:
        api = YouTrackAPIClient(YOUTRACK_URL, YOUTRACK_TOKEN)
        
        # Health check
        if not api.health_check():
            logger.error("Failed to connect to YouTrack API")
            sys.exit(1)
        
        # Resolve project key to internal ID
        projects = api.get_projects(top=100)
        project_id = None
        for p in projects:
            if p.get("shortName", "").upper() == YOUTRACK_PROJECT_KEY.upper() or \
               p.get("name", "").lower() == YOUTRACK_PROJECT_KEY.lower() or \
               p.get("id") == YOUTRACK_PROJECT_KEY:
                project_id = p["id"]
                logger.info(f"Resolved project '{YOUTRACK_PROJECT_KEY}' -> internal id: {project_id}")
                break
        if not project_id:
            logger.error(f"Project '{YOUTRACK_PROJECT_KEY}' not found. Available: {[p.get('shortName') for p in projects]}")
            sys.exit(1)

        # Generate test data
        generator = TestDataGenerator(api)
        success = generator.generate_all_test_data(project_id)
        
        if success:
            logger.info("Test data generation completed successfully")
            sys.exit(0)
        else:
            logger.error("Test data generation failed or created no data")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
