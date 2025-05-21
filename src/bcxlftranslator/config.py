import argparse

def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', nargs='?')
    parser.add_argument('output_file', nargs='?')
    args = parser.parse_args()
    config_dict = {
        'input_file': args.input_file,
        'output_file': args.output_file,
    }
    return config_dict
