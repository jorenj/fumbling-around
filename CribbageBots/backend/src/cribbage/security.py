import hashlib
import marshal
import types
from . import engine, rules, models

def get_runtime_signature():
    """
    Calculates a combined SHA-256 hash of the bytecode of core engine functions.
    This detects in-memory monkey-patching of game logic.
    """
    hasher = hashlib.sha256()
    
    # Modules to protect
    modules = [engine, rules, models]
    
    for module in modules:
        # Sort keys to ensure deterministic hashing
        for name in sorted(dir(module)):
            obj = getattr(module, name)
            
            # Hash functions
            if isinstance(obj, types.FunctionType):
                hasher.update(marshal.dumps(obj.__code__))
            
            # Hash classes (including their methods)
            elif isinstance(obj, type):
                for attr_name in sorted(dir(obj)):
                    attr_obj = getattr(obj, attr_name)
                    if isinstance(attr_obj, (types.FunctionType, types.MethodType)):
                        if hasattr(attr_obj, "__code__"):
                            hasher.update(marshal.dumps(attr_obj.__code__))
                            
    return hasher.hexdigest()

def get_engine_signature():
    """Legacy alias for backward compatibility."""
    return get_runtime_signature()

def filter_event_for_player(event: dict, player_id: str) -> dict:
    """
    Scrubs sensitive information from a single event for a specific recipient.
    The recipient keeps their own hand data; the opponent's is stripped.
    Used in the human WebSocket path where the player must see their own hand.

    SEC-1: Prevents leakage of opponent hand contents in count_hand_request events.
    """
    if event.get("type") == "count_hand_request":
        # Strip hand data only if this event belongs to someone else
        if event.get("player_id") != player_id:
            scrubbed = event.copy()
            if "data" in scrubbed:
                scrubbed["data"] = scrubbed["data"].copy()
                scrubbed["data"].pop("hand", None)
                scrubbed["data"].pop("is_crib", None)
                scrubbed["data"]["message"] = "[REDACTED: Opponent Hand]"
            return scrubbed

    return event


def scrub_log_for_observer(log: list) -> list:
    """
    Strips ALL hand contents from count_hand_request events in a game log,
    producing a neutral observer log safe to return to any API caller.

    This is distinct from filter_event_for_player, which is per-player aware.
    Use this for the REST /api/tournament response, where the caller is an
    unknown third party (e.g. the dashboard UI) and should not receive either
    player's hand or crib card data.

    SEC-1: Prevents any API caller from harvesting opponent hand data from
    the returned game log.
    """
    result = []
    for event in log:
        if event.get("type") == "count_hand_request":
            scrubbed = event.copy()
            if "data" in scrubbed:
                scrubbed["data"] = scrubbed["data"].copy()
                scrubbed["data"].pop("hand", None)
                scrubbed["data"].pop("is_crib", None)
                scrubbed["data"]["message"] = "[REDACTED: Hand Contents]"
            result.append(scrubbed)
        else:
            result.append(event)
    return result
