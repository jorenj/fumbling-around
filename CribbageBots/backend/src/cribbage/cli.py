import argparse
import sys
import os

from .tournament import run_tournament
from .bots import BOT_REGISTRY

def main():
    parser = argparse.ArgumentParser(description="Cribbage Tournament CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a tournament between two bots")
    run_parser.add_argument("--p1", choices=BOT_REGISTRY.keys(), default="random", help="Bot type for Player 1")
    run_parser.add_argument("--p2", choices=BOT_REGISTRY.keys(), default="greedy", help="Bot type for Player 2")
    run_parser.add_argument("--games", type=int, default=10, help="Number of games to play")
    run_parser.add_argument("--verbose", action="store_true", help="Print detailed game events")

    # API command
    api_parser = subparsers.add_parser("api", help="Start the FastAPI server")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")

    args = parser.parse_args()

    if args.command == "run":
        p1_class = BOT_REGISTRY[args.p1]["class"]
        p2_class = BOT_REGISTRY[args.p2]["class"]
        p1_id = args.p1.capitalize() + "Bot 1"
        p2_id = args.p2.capitalize() + "Bot 2"
        print(f"Starting tournament: {p1_id} vs {p2_id} ({args.games} games)")
        run_tournament(p1_class, p2_class, num_games=args.games, verbose=args.verbose, p1_id=p1_id, p2_id=p2_id)
    
    elif args.command == "api":
        import uvicorn
        print(f"Starting API server on {args.host}:{args.port}")
        uvicorn.run("cribbage.api:app", host=args.host, port=args.port, reload=True)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
