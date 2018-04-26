import json
import subprocess

import os

PROFILE_FILE = 'profile.json'
SOURCES_ID_FILE = 'sources_id.json'
DESTS_ID_FILE = 'dests_id.json'
FRONTEND_FIXTURES_FILE = 'frontend_fixtures.json'
FLOW_REQUEST_DATA_FILE = 'flow_requests_data_{}.json'
CONSENT_CONFIRM_FILE = 'consent_confirmation_data_{}.json'
ENDPOINTS_FILE = 'endpoints.json'
CONSENTS_FILE = 'consents_{}.json'
BACKEND_FIXTURES_FILE = 'backend_fixtures.json'
CONSENT_MANAGER_DB = 'consent_manager.db'
BACKEND_DB = 'backend.db'
FRONTEND_DB = 'frontend.db'


def docker_compose_exec(service, *cmd, env=None):
    cmd = ['docker-compose', 'exec', service] + list(cmd)
    print(cmd)
    subprocess.run(cmd, check=True, env=env)


def get_sources(input_dir):
    with open(os.path.join(input_dir, SOURCES_ID_FILE)) as f:
        return json.load(f)


def get_destinations(input_dir):
    with open(os.path.join(input_dir, DESTS_ID_FILE)) as f:
        return json.load(f)
