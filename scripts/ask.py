"""CLI for the application agent: ping the user on Discord and (optionally) wait for a reply.

Exit codes: 0 done/answered/cached/sent, 2 skipped, 3 timeout, 4 no_reader, 1 error.
The result JSON is printed as the last stdout line.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import discord_io

EXIT = {"skipped": 2, "timeout": 3, "no_reader": 4, "error": 1}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--kind", required=True, choices=discord_io.KINDS)
    p.add_argument("--company", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--detail", required=True)
    p.add_argument("--url")
    p.add_argument("--timeout", type=float, default=7200)
    p.add_argument("--interval", type=float, default=20)
    p.add_argument("--no-wait", action="store_true", help="just ping, do not wait for a reply")
    a = p.parse_args(argv)
    try:
        res = discord_io.ask(a.kind, a.company, a.title, a.detail, a.url,
                             a.timeout, a.interval, wait=not a.no_wait)
    except Exception as e:  # message never contains secrets
        res = {"status": "error", "text": str(e), "message_id": ""}
    print(json.dumps(res))
    return EXIT.get(res["status"], 0)


if __name__ == "__main__":
    sys.exit(main())
