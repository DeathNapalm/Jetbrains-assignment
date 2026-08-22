"""
YouTrack REST API client module.
Handles authentication, user management, project team management, and issue creation.
"""
import requests
import logging
import time
from typing import Dict, List, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class YouTrackAPIClient:
    """Client for interacting with YouTrack REST API."""

    def __init__(self, base_url: str, token: str, timeout: int = 30, max_retries: int = 3):
        """
        Initialize YouTrack API client.
        
        Args:
            base_url: YouTrack base URL (e.g., http://localhost:8080)
            token: Permanent token for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = self._create_session(max_retries)

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get headers for API request."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": content_type,
        }

    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
        content_type: str = "application/json"
    ) -> Dict[str, Any]:
        """
        Make HTTP request to YouTrack API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            files: Files for multipart upload
            content_type: Content-Type header value
            
        Returns:
            Response JSON data
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}/api{endpoint}"
        headers = self._get_headers(content_type) if files is None else self._get_headers("multipart/form-data")
        if files:
            headers.pop("Content-Type", None)  # Let requests set it for multipart
            
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if data and files is None else None,
                data=data if data and files else None,
                params=params,
                files=files,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Return empty dict for 204 No Content
            if response.status_code == 204:
                return {}
                
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise

    # User Management

    def create_user(self, login: str, name: str, email: str, password: str = "YouTrack123!") -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            login: User login/username
            name: User full name
            email: User email address
            password: Initial password (required by YouTrack)
            
        Returns:
            Created user data
        """
        data = {
            "login": login,
            "fullName": name,
            "email": email,
            "password": password,
        }
        logger.debug(f"Creating user: {login}")
        return self._make_request("POST", "/users", data=data)

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user details."""
        return self._make_request("GET", f"/users/{user_id}")

    def get_users(self, skip: int = 0, top: int = 100) -> Dict[str, Any]:
        """Get list of users with pagination."""
        params = {"$skip": skip, "$top": top}
        return self._make_request("GET", "/users", params=params)

    def add_user_to_group(self, user_id: str, group_id: str) -> Dict[str, Any]:
        """Add user to a group."""
        logger.debug(f"Adding user {user_id} to group {group_id}")
        return self._make_request("POST", f"/users/{user_id}/groups", data={"id": group_id})

    # Group Management

    def get_group(self, group_name: str) -> Optional[Dict[str, Any]]:
        """Get group by name."""
        try:
            return self._make_request("GET", f"/groups", params={"query": f'name: "{group_name}"'})
        except requests.RequestException:
            return None

    def create_group(self, name: str) -> Dict[str, Any]:
        """Create a new group."""
        data = {"name": name}
        logger.info(f"Creating group: {name}")
        return self._make_request("POST", "/groups", data=data)

    # Project Team Management

    def add_user_to_project_team(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Add user to project team."""
        logger.debug(f"Adding user {user_id} to project team {project_id}")
        data = {"users": [{"id": user_id}]}
        return self._make_request("POST", f"/admin/projects/{project_id}/team", data=data)

    def get_project_team(self, project_id: str, skip: int = 0, top: int = 100) -> Dict[str, Any]:
        """Get project team members."""
        params = {"$skip": skip, "$top": top}
        return self._make_request("GET", f"/admin/projects/{project_id}/team", params=params)

    def grant_project_permissions(
        self, 
        project_id: str, 
        user_id: str, 
        permissions: List[str]
    ) -> Dict[str, Any]:
        """Grant permissions to user in project."""
        logger.debug(f"Granting permissions to user {user_id} in project {project_id}")
        data = {"permissions": permissions}
        return self._make_request("POST", f"/projects/{project_id}/team/{user_id}/permissions", data=data)

    # Project Management

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        return self._make_request("GET", f"/projects/{project_id}")

    def get_projects(self, skip: int = 0, top: int = 10) -> list:
        """Get list of projects."""
        params = {"$skip": skip, "$top": top, "fields": "id,name,shortName"}
        return self._make_request("GET", "/admin/projects", params=params)

    # Issue Management

    def create_issue(
        self,
        summary: str,
        description: str,
        project_id: str,
        reporter_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new issue.
        
        Args:
            summary: Issue title/summary
            description: Issue description
            project_id: Project ID
            reporter_id: Reporter user ID (optional)
            assignee_id: Assignee user ID (optional)
            **kwargs: Additional fields
            
        Returns:
            Created issue data
        """
        data = {
            "summary": summary,
            "description": description,
            "project": {"id": project_id}
        }
        
        if reporter_id:
            data["reporter"] = {"id": reporter_id}
        if assignee_id:
            data["assignee"] = {"id": assignee_id}
            
        # Add any additional fields
        data.update(kwargs)
        
        return self._make_request("POST", "/issues", data=data)

    def get_issue(self, issue_id: str, fields: Optional[str] = None) -> Dict[str, Any]:
        """Get issue details."""
        params = {}
        if fields:
            params["fields"] = fields
        return self._make_request("GET", f"/issues/{issue_id}", params=params)

    def get_issues(
        self,
        query: Optional[str] = None,
        fields: Optional[str] = None,
        skip: int = 0,
        top: int = 100
    ) -> Dict[str, Any]:
        """Get list of issues with optional query and pagination."""
        params = {"$skip": skip, "$top": top}
        if query:
            params["query"] = query
        if fields:
            params["fields"] = fields
        return self._make_request("GET", "/issues", params=params)

    def update_issue(self, issue_id: str, **kwargs) -> Dict[str, Any]:
        """Update issue with specified fields."""
        logger.debug(f"Updating issue {issue_id}")
        return self._make_request("POST", f"/issues/{issue_id}", data=kwargs)

    def add_issue_comment(self, issue_id: str, text: str) -> Dict[str, Any]:
        """Add comment to issue."""
        data = {"text": text}
        logger.debug(f"Adding comment to issue {issue_id}")
        return self._make_request("POST", f"/issues/{issue_id}/comments", data=data)

    def add_issue_tag(self, issue_id: str, tag_name: str) -> Dict[str, Any]:
        """Add tag to issue."""
        data = {"name": tag_name}
        logger.debug(f"Adding tag '{tag_name}' to issue {issue_id}")
        return self._make_request("POST", f"/issues/{issue_id}/tags", data=data)

    def link_issues(self, issue_id: str, linked_issue_id: str, link_type: str = "relates to") -> Dict[str, Any]:
        """Link two issues."""
        data = {
            "issue": {"id": linked_issue_id},
            "linkType": {"name": link_type}
        }
        logger.debug(f"Linking issue {issue_id} to {linked_issue_id}")
        return self._make_request("POST", f"/issues/{issue_id}/links", data=data)

    # Database Management

    def create_backup(self) -> Dict[str, Any]:
        """Trigger database backup."""
        logger.info("Initiating database backup")
        data = {"backupStatus": {"backupInProgress": True, "stopBackup": False}}
        params = {"fields": "backupStatus(backupInProgress,backupCancelled,backupError(date,errorMessage),stopBackup)"}
        return self._make_request("POST", "/admin/databaseBackup/settings", data=data, params=params)

    def get_backup_status(self) -> Dict[str, Any]:
        """Get backup status."""
        params = {"fields": "backupStatus(backupInProgress,backupCancelled,backupError(date,errorMessage),stopBackup)"}
        return self._make_request("GET", "/admin/databaseBackup/settings", params=params)

    # Health Check

    def health_check(self) -> bool:
        """Check if YouTrack API is accessible."""
        try:
            self._make_request("GET", "/issues", params={"$top": 1})
            logger.info("YouTrack API health check passed")
            return True
        except requests.RequestException as e:
            logger.error(f"YouTrack API health check failed: {e}")
            return False
