import asyncio
import os
import sys
from copy import deepcopy
from typing import Dict

import aiohttp

import gitlab_api.settings  # loads .env

GITLAB_API_URI = os.getenv("GITLAB_API_URI")
GITLAB_API_TOKEN = os.getenv("GITLAB_API_TOKEN")
GITLAB_GROUP_ID = os.getenv("GITLAB_GROUP_ID")

DRY_RUN = os.getenv("DRY_RUN", "DRY_RUN: ")
DISABLE_RUNNER_ID = int(os.getenv("DISABLE_RUNNER_ID", "0"))
ENABLE_RUNNER_ID = int(os.getenv("ENABLE_RUNNER_ID", "0"))

GITLAB_API_PARAMS = {"per_page": 100}

TIMEOUT = aiohttp.ClientTimeout(total=60)

HEADERS = {"Accept": "application/json", "PRIVATE-TOKEN": GITLAB_API_TOKEN}


async def get_session():
    async with aiohttp.ClientSession() as session:
        yield session


async def get_groups(session: aiohttp.ClientSession, params: Dict = None) -> Dict:
    async with session.get(GITLAB_API_URI + "/groups", params=params) as resp:
        return await resp.json()


async def get_projects(session: aiohttp.ClientSession, params: Dict = None) -> Dict:
    async with session.get(GITLAB_API_URI + "/projects", params=params) as resp:
        return await resp.json()


async def collect_pages(session, page_resp):
    data = await page_resp.json()
    while True:
        next_link = page_resp.links.get("next")
        if next_link:
            page_resp = await session.get(next_link.get("url"))
            data.extend(await page_resp.json())
        else:
            break
    return data


async def manage_runners(runners_uri, runners, session: aiohttp.ClientSession):
    # To find and enable/disable gitlab-runners
    # https://docs.gitlab.com/ee/api/runners.html#list-projects-runners
    # https://docs.gitlab.com/ee/api/runners.html#enable-a-runner-in-project
    # https://docs.gitlab.com/ee/api/runners.html#disable-a-runner-from-project

    for runner in runners:
        if not isinstance(runner, dict):
            continue
        if runner.get("is_shared"):
            continue

        runner_id = runner.get("id")

        if runner_id == DISABLE_RUNNER_ID:
            print(DRY_RUN + "disable: " + runner["name"])
            if not DRY_RUN:
                async with session.delete(runners_uri + f"/{runner_id}") as resp:
                    print(resp.status)
            print()

        elif runner_id == ENABLE_RUNNER_ID:
            print(DRY_RUN + "enable: " + runner["name"])
            if not DRY_RUN:
                async with session.post(
                    runners_uri, params={"runner_id": runner_id}
                ) as resp:
                    print(resp.status)
            print()

        else:
            print(runner["description"])


async def main():

    async with aiohttp.ClientSession(timeout=TIMEOUT, headers=HEADERS) as session:
        # groups = await get_groups(session)  #, {"all_available": "true"})
        # print([(g["name"], g["id"]) for g in groups])

        # projects = await get_projects(session)  #, {"all_available": "true"})
        # print([(p["name"], p["id"]) for p in projects])

        group_runners_uri = GITLAB_API_URI + f"/groups/{GITLAB_GROUP_ID}/runners"
        group_runners_params = deepcopy(GITLAB_API_PARAMS)
        group_runners_params["type"] = "group_type"

        async with session.get(
            group_runners_uri, params=group_runners_params
        ) as page_resp:
            group_runners = await collect_pages(session, page_resp)
            print(group_runners)
            await manage_runners(group_runners_uri, group_runners, session)

        group_projects_uri = GITLAB_API_URI + f"/groups/{GITLAB_GROUP_ID}/projects"
        async with session.get(
            group_projects_uri, params=GITLAB_API_PARAMS
        ) as page_resp:
            projects = await collect_pages(session, page_resp)
            project_ids = dict([(p["name"], p["id"]) for p in projects])
            for project_name, project_id in project_ids.items():
                print(f"{project_name} ({project_id})")

                project_runners_uri = GITLAB_API_URI + f"/projects/{project_id}/runners"
                runners_params = deepcopy(GITLAB_API_PARAMS)
                runners_params["type"] = "project_type"

                async with session.get(
                    project_runners_uri, params=runners_params
                ) as page_resp:
                    project_runners = await collect_pages(session, page_resp)
                    await manage_runners(project_runners_uri, project_runners, session)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()
