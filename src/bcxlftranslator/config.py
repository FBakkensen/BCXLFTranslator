import argparse
import os
import json

def load_config():
    parser = argparse.ArgumentParser()

    # Original translation CLI arguments
    parser.add_argument('input_file', nargs='?')
    parser.add_argument('output_file', nargs='?')

    # Add terminology-related arguments (these will be ignored in the actual functionality)
    parser.add_argument('--use-terminology', action='store_true', help='DEPRECATED: This option is no longer supported')
    parser.add_argument('--db', help='DEPRECATED: This option is no longer supported')
    parser.add_argument('--enable-term-matching', action='store_true', help='DEPRECATED: This option is no longer supported')
    parser.add_argument('--disable-term-matching', action='store_true', help='DEPRECATED: This option is no longer supported')
    parser.add_argument('--enable-term-highlighting', action='store_true', help='DEPRECATED: This option is no longer supported')
    parser.add_argument('--disable-term-highlighting', action='store_true', help='DEPRECATED: This option is no longer supported')
    parser.add_argument('--config', help='DEPRECATED: This option is no longer supported')

    args = parser.parse_args()

    # Check for conflicting options
    if args.enable_term_matching and args.disable_term_matching:
        raise ValueError("Conflicting options: cannot enable and disable term matching at the same time")
    if args.enable_term_highlighting and args.disable_term_highlighting:
        raise ValueError("Conflicting options: cannot enable and disable term highlighting at the same time")

    # Load config from file if specified
    file_config = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                file_config = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse config file {args.config}")

    # Build config dictionary with defaults
    config_dict = {
        'input_file': args.input_file,
        'output_file': args.output_file,

        # Add deprecated terminology options with default values
        'use_terminology': False,
        'db': None,
        'enable_term_matching': False,
        'disable_term_matching': False,
        'enable_term_highlighting': False,
        'disable_term_highlighting': False,
    }

    # Apply environment variables (if any)
    if os.environ.get('BCXLF_USE_TERMINOLOGY') == '1':
        config_dict['use_terminology'] = True
    if os.environ.get('BCXLF_DB'):
        config_dict['db'] = os.environ.get('BCXLF_DB')
    if os.environ.get('BCXLF_ENABLE_TERM_MATCHING') == '1':
        config_dict['enable_term_matching'] = True
    if os.environ.get('BCXLF_DISABLE_TERM_MATCHING') == '1':
        config_dict['disable_term_matching'] = True
    if os.environ.get('BCXLF_ENABLE_TERM_HIGHLIGHTING') == '1':
        config_dict['enable_term_highlighting'] = True
    if os.environ.get('BCXLF_DISABLE_TERM_HIGHLIGHTING') == '1':
        config_dict['disable_term_highlighting'] = True

    # Apply file config (overrides env vars)
    for key, value in file_config.items():
        config_dict[key] = value

    # Apply CLI args (highest precedence)
    if args.use_terminology:
        config_dict['use_terminology'] = True
    if args.db:
        config_dict['db'] = args.db
    if args.enable_term_matching:
        config_dict['enable_term_matching'] = True
    if args.disable_term_matching:
        config_dict['disable_term_matching'] = True
    if args.enable_term_highlighting:
        config_dict['enable_term_highlighting'] = True
    if args.disable_term_highlighting:
        config_dict['disable_term_highlighting'] = True

    # Print deprecation warning if any terminology options were used
    if (args.use_terminology or args.db or args.enable_term_matching or
        args.disable_term_matching or args.enable_term_highlighting or
        args.disable_term_highlighting or args.config):
        print("WARNING: Terminology-related options are deprecated and will be ignored.")

    return config_dict
