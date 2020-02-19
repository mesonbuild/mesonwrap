import argparse

from wrapweb import APP


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--secret-key')
    parser.add_argument('--db-directory')
    parser.add_argument('--mode', help='cache or standalone')
    parser.add_argument('--github-token')
    args = parser.parse_args(args)
    for opt in ['secret_key', 'db_directory', 'mode', 'github_token']:
        if getattr(args, opt):
            APP.config[opt.upper()] = getattr(args, opt)
    APP.run(host=args.host,
            port=args.port,
            debug=True)
