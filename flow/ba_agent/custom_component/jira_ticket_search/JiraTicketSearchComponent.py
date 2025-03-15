from typing import Any, Sequence, Dict, Optional, List
import requests
from langchain_core.tools import Tool
from loguru import logger

from langflow.base.langchain_utilities.model import LCToolComponent
from langflow.inputs import MessageTextInput, SecretStrInput, DropdownInput, IntInput, BoolInput


class JiraSearchTicketComponent(LCToolComponent):
    display_name: str = "Jira Search Tickets"
    description: str = "Search tickets in Jira based on various criteria"
    name = "JiraSearchTickets"
    icon = "Jira"
    documentation: str = "https://docs.langflow.org"

    inputs = [
        MessageTextInput(
            name="jira_instance",
            display_name="Jira Instance URL",
            value="",
            info="The URL of your Jira instance (e.g., https://your-domain.atlassian.net)",
        ),
        SecretStrInput(
            name="api_token",
            display_name="API Token",
            value="",
            info="Your Jira API token",
            password=True,
        ),
        MessageTextInput(
            name="username",
            display_name="Username/Email",
            value="",
            info="Your Jira username or email",
        ),
        DropdownInput(
            name="search_type",
            display_name="Search Type",
            options=["jql", "text", "key", "specific_id", "assignee", "reporter", "status", "all"],
            value="all",
            info="The type of search to perform",
        ),
        IntInput(
            name="max_results",
            display_name="Maximum Results",
            value=10,
            info="Maximum number of results to return",
        ),
        BoolInput(
            name="include_comments",
            display_name="Include Comments",
            value=False,
            info="Include ticket comments in the results",
        ),
        BoolInput(
            name="include_attachments",
            display_name="List Attachments",
            value=False,
            info="Include attachment information in the results",
            advanced=True,
        ),
    ]

    def _search_by_jql(self, jql_query: str) -> List[Dict]:
        """Search tickets using JQL (Jira Query Language)."""
        url = f"{self.jira_instance}/rest/api/2/search"
        params = {
            "jql": jql_query,
            "maxResults": self.max_results
        }
        response = self._make_request(url, params=params)
        return self._process_search_results(response.get("issues", []))

    def _search_by_text(self, text: str) -> List[Dict]:
        """Search tickets containing specific text."""
        jql_query = f'text ~ "{text}"'
        return self._search_by_jql(jql_query)

    def _search_by_key(self, key: str) -> List[Dict]:
        """Search for a specific ticket by its key."""
        # Clean up the key to handle potential formatting issues
        key = key.strip().upper()

        # First try direct ticket lookup
        url = f"{self.jira_instance}/rest/api/2/issue/{key}"
        try:
            response = self._make_request(url)
            return [self._process_ticket(response)]
        except Exception as e:
            logger.warning(f"Direct ticket lookup failed: {e}")
            # Fall back to JQL search
            jql_query = f'key = "{key}"'
            return self._search_by_jql(jql_query)

    def _search_by_specific_id(self, ticket_id: str) -> List[Dict]:
        """Search for a specific ticket by ID like OAPI-10686."""
        # Ensure the ticket ID is properly formatted
        ticket_id = ticket_id.strip().upper()

        # Get the ticket directly by its key
        return self._search_by_key(ticket_id)

    def _search_by_assignee(self, assignee: str) -> List[Dict]:
        """Search tickets assigned to a specific user."""
        jql_query = f'assignee = "{assignee}"'
        return self._search_by_jql(jql_query)

    def _search_by_reporter(self, reporter: str) -> List[Dict]:
        """Search tickets reported by a specific user."""
        jql_query = f'reporter = "{reporter}"'
        return self._search_by_jql(jql_query)

    def _search_by_status(self, status: str) -> List[Dict]:
        """Search tickets with a specific status."""
        jql_query = f'status = "{status}"'
        return self._search_by_jql(jql_query)

    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """Make an authenticated request to the Jira API."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = requests.get(
            url,
            auth=(self.username, self.api_token),
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            raise ValueError(f"Jira API request failed: {response.status_code} - {response.text}")

        return response.json()

    def _get_comments(self, ticket_key: str) -> List[Dict]:
        """Get comments for a specific ticket."""
        if not self.include_comments:
            return []

        url = f"{self.jira_instance}/rest/api/2/issue/{ticket_key}/comment"
        response = self._make_request(url)

        comments = []
        for comment in response.get("comments", []):
            comments.append({
                "author": comment.get("author", {}).get("displayName", "Unknown"),
                "created": comment.get("created"),
                "body": comment.get("body")
            })

        return comments

    def _get_attachments(self, ticket_key: str) -> List[Dict]:
        """Get attachment information for a specific ticket."""
        if not self.include_attachments:
            return []

        url = f"{self.jira_instance}/rest/api/2/issue/{ticket_key}"
        response = self._make_request(url)

        attachments = []
        for attachment in response.get("fields", {}).get("attachment", []):
            attachments.append({
                "filename": attachment.get("filename"),
                "size": attachment.get("size"),
                "created": attachment.get("created"),
                "url": attachment.get("content")
            })

        return attachments

    def _process_ticket(self, ticket: Dict) -> Dict:
        """Process a ticket to extract relevant information."""
        ticket_key = ticket.get("key")
        fields = ticket.get("fields", {})

        processed_ticket = {
            "key": ticket_key,
            "summary": fields.get("summary"),
            "description": fields.get("description"),
            "status": fields.get("status", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
            "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else "Unknown",
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "url": f"{self.jira_instance}/browse/{ticket_key}"
        }

        if self.include_comments:
            processed_ticket["comments"] = self._get_comments(ticket_key)

        if self.include_attachments:
            processed_ticket["attachments"] = self._get_attachments(ticket_key)

        return processed_ticket

    def _process_search_results(self, issues: List[Dict]) -> List[Dict]:
        """Process search results to extract relevant information."""
        processed_results = []

        for issue in issues:
            processed_results.append(self._process_ticket(issue))

        return processed_results

    def _format_search_results(self, results: List[Dict]) -> str:
        """Format search results as a readable string."""
        if not results:
            return "No tickets found."

        formatted_results = []

        for ticket in results:
            ticket_info = [
                f"Key: {ticket['key']}",
                f"Summary: {ticket['summary']}",
                f"Status: {ticket['status']}",
                f"Assignee: {ticket['assignee']}",
                f"Reporter: {ticket['reporter']}",
                f"URL: {ticket['url']}"
            ]

            if self.include_comments and ticket.get("comments"):
                comments_info = ["Comments:"]
                for comment in ticket["comments"]:
                    comments_info.append(f"  - {comment['author']} ({comment['created']}): {comment['body'][:100]}...")
                ticket_info.append("\n".join(comments_info))

            if self.include_attachments and ticket.get("attachments"):
                attachments_info = ["Attachments:"]
                for attachment in ticket["attachments"]:
                    attachments_info.append(f"  - {attachment['filename']} ({attachment['size']} bytes)")
                ticket_info.append("\n".join(attachments_info))

            formatted_results.append("\n".join(ticket_info))

        return "\n\n".join(formatted_results)

    def build_tool(self) -> Sequence[Tool]:
        """Build and return Jira search tools based on selected search type."""
        tools = []

        if self.search_type in ["jql", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_JQL",
                    description="Search Jira tickets using JQL (Jira Query Language). Input should be a valid JQL query string.",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_jql(input_str.strip())
                    ),
                )
            )

        if self.search_type in ["text", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_Text",
                    description="Search Jira tickets containing specific text. Input should be the text to search for.",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_text(input_str.strip())
                    ),
                )
            )

        if self.search_type in ["key", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_Key",
                    description="Search for a specific Jira ticket by its key (e.g., PROJECT-123).",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_key(input_str.strip())
                    ),
                )
            )

        if self.search_type in ["specific_id", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_Specific_ID",
                    description="Search for a specific Jira ticket by its ID (e.g., OAPI-10686).",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_specific_id(input_str.strip())
                    ),
                )
            )

        if self.search_type in ["assignee", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_Assignee",
                    description="Search Jira tickets assigned to a specific user. Input should be the username or email.",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_assignee(input_str.strip())
                    ),
                )
            )

        if self.search_type in ["reporter", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_Reporter",
                    description="Search Jira tickets reported by a specific user. Input should be the username or email.",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_reporter(input_str.strip())
                    ),
                )
            )

        if self.search_type in ["status", "all"]:
            tools.append(
                Tool(
                    name="Jira_Search_Status",
                    description="Search Jira tickets with a specific status. Input should be the status name (e.g., 'In Progress', 'Done').",
                    func=lambda input_str: self._format_search_results(
                        self._search_by_status(input_str.strip())
                    ),
                )
            )

        return tools

    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:
        """Update build configuration based on field changes."""
        # No dynamic updates needed for this component
        return build_config