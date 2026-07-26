import httpx
from typing import List, Optional
from fastapi import HTTPException
from models.github import GitHubProfileInfo, RepositoryInfo


class GitHubService:
    BASE_URL = "https://api.github.com"

    @classmethod
    async def fetch_user_profile(cls, username: str) -> GitHubProfileInfo:
        """
        Fetches GitHub profile information using the GitHub REST API.
        """
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{cls.BASE_URL}/users/{username}", headers=headers)

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found")
            if response.status_code == 403:
                raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded. Please try again later.")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GitHub API Error: {response.text}"
                )

            data = response.json()
            return GitHubProfileInfo(
                username=data.get("login", username),
                name=data.get("name") or data.get("login", username),
                avatar_url=data.get("avatar_url"),
                bio=data.get("bio"),
                public_repos=data.get("public_repos", 0),
                followers=data.get("followers", 0),
                following=data.get("following", 0),
                html_url=data.get("html_url")
            )

    @classmethod
    async def fetch_user_repositories(cls, username: str, limit: int = 15) -> List[RepositoryInfo]:
        """
        Fetches user repositories sorted by recently updated, along with language, stars, forks, and readme/description.
        """
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{cls.BASE_URL}/users/{username}/repos?per_page=100&sort=updated",
                headers=headers
            )

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub user not found")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GitHub API Error: {response.text}"
                )

            repos_data = response.json()
            # Sort repos by stargazers_count and recently updated
            sorted_repos = sorted(
                repos_data,
                key=lambda r: (r.get("stargazers_count", 0), r.get("updated_at", "")),
                reverse=True
            )[:limit]

            repositories: List[RepositoryInfo] = []
            for r in sorted_repos:
                desc = r.get("description") or ""
                repo_info = RepositoryInfo(
                    name=r.get("name", "Unknown"),
                    description=desc,
                    html_url=r.get("html_url"),
                    language=r.get("language") or "Other",
                    stargazers_count=r.get("stargazers_count", 0),
                    forks_count=r.get("forks_count", 0),
                    updated_at=r.get("updated_at"),
                    readme_snippet=desc
                )
                repositories.append(repo_info)

            return repositories
