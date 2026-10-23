# ReelLore AI - Multi-Agent Game Lore & Dev-Log Instagram Reel Generator
import os

# Disable telemetry and prompts to ensure clean automated execution
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"

# Safe patch for Groq API endpoint compatibility:
# Groq strict schema rejects 'cache_breakpoint' property on system/user messages.
try:
    import crewai.llms.cache
    crewai.llms.cache.mark_cache_breakpoint = lambda m: m
except Exception:
    pass
