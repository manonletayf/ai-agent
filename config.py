from utils.env_loader import load_environment
import os

load_environment()

CORESIGNAL_API_KEY = os.getenv("CORESIGNAL_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
