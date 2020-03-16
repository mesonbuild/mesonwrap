import argparse

from mesonwrap.tools import environment
from wrapweb import APP


def main(prog, args):
    parser = argparse.ArgumentParser(prog)
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--secret-key')
    parser.add_argument('--github-token')
    parser.add_argument('--github-token-env', action='store_true')
    args = parser.parse_args(args)
    for opt in ['secret_key', 'github_token']:
        if getattr(args, opt):
            APP.config[opt.upper()] = getattr(args, opt)
    if args.github_token_env:
        APP.config['GITHUB_TOKEN'] = environment.Config().github_token
    APP.run(host=args.host,
            port=args.port,
            debug=True)
