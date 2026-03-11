"""Pipeline config from env."""
import os

ROOT_DIR = os.environ.get("ROOT_DIR", os.getcwd())
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_CLIENT = os.environ.get("LLM_CLIENT", "anthropic").lower()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://claudible.io/v1")
DRY_RUN = os.environ.get("PIPELINE_DRY_RUN", "").lower() in ("1", "true", "yes")
VERBOSE = os.environ.get("PIPELINE_VERBOSE", "").lower() in ("1", "true", "yes")
JENKINS_URL = os.environ.get("JENKINS_URL", "")
JENKINS_JOB = os.environ.get("JENKINS_JOB", "")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")
MAX_ITERATIONS = 2
MAX_FILES = 15
MAX_CHARS_PER_FILE = 8000
