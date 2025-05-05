import argparse
import os
import json

def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--use-terminology', action='store_true')
    parser.add_argument('--db', type=str)
    parser.add_argument('--enable-term-matching', action='store_true')
    parser.add_argument('--disable-term-matching', action='store_true')
    parser.add_argument('--enable-term-highlighting', action='store_true')
    parser.add_argument('--disable-term-highlighting', action='store_true')
    parser.add_argument('--config', type=str, help='Path to configuration file (JSON)')
    parser.add_argument('input_file', nargs='?')
    parser.add_argument('output_file', nargs='?')
    args = parser.parse_args()
    file_config = {}
    if args.config:
        with open(args.config, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
    env_config = {
        'use_terminology': os.getenv('BCXLF_USE_TERMINOLOGY'),
        'db': os.getenv('BCXLF_DB'),
        'enable_term_matching': os.getenv('BCXLF_ENABLE_TERM_MATCHING'),
        'disable_term_matching': os.getenv('BCXLF_DISABLE_TERM_MATCHING'),
        'enable_term_highlighting': os.getenv('BCXLF_ENABLE_TERM_HIGHLIGHTING'),
        'disable_term_highlighting': os.getenv('BCXLF_DISABLE_TERM_HIGHLIGHTING'),
    }
    def parse_bool(val):
        if isinstance(val, bool):
            return val
        if val is None:
            return False
        return str(val).lower() in ('1', 'true', 'yes', 'on')
    config_dict = {
        'use_terminology': args.use_terminology or file_config.get('use_terminology') or parse_bool(env_config['use_terminology']) or False,
        'db': args.db or file_config.get('db') or env_config['db'],
        'enable_term_matching': args.enable_term_matching or file_config.get('enable_term_matching') or parse_bool(env_config['enable_term_matching']) or False,
        'disable_term_matching': args.disable_term_matching or file_config.get('disable_term_matching') or parse_bool(env_config['disable_term_matching']) or False,
        'enable_term_highlighting': args.enable_term_highlighting or file_config.get('enable_term_highlighting') or parse_bool(env_config['enable_term_highlighting']) or False,
        'disable_term_highlighting': args.disable_term_highlighting or file_config.get('disable_term_highlighting') or parse_bool(env_config['disable_term_highlighting']) or False,
        'input_file': args.input_file,
        'output_file': args.output_file,
    }
    # Validation: conflicting enable/disable for same feature
    if config_dict['enable_term_matching'] and config_dict['disable_term_matching']:
        raise ValueError("Cannot specify both enable and disable for term matching.")
    if config_dict['enable_term_highlighting'] and config_dict['disable_term_highlighting']:
        raise ValueError("Cannot specify both enable and disable for term highlighting.")
    return config_dict
