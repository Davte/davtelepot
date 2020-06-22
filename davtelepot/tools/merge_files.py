"""Use this tool to merge davtelepot-split files.

Documents larger than 50 MB are automatically split by `send_document` method
    and can be merged with this tool.
Example:
python3 -m davtelepot.tools.merge_files my_file.pdf
"""

import argparse
import glob
import logging
import os


def merge_files(input_file_path, output_file_path):
    input_directory = os.path.dirname(os.path.abspath(input_file_path))
    input_file_name = os.path.basename(os.path.abspath(input_file_path))
    if output_file_path:
        output_directory = os.path.dirname(os.path.abspath(output_file_path))
        output_file_name = os.path.basename(os.path.abspath(output_file_path))
    else:
        output_directory = input_directory
        output_file_name = input_file_name + 'out'
    with open(os.path.join(output_directory, output_file_name), 'wb') as output_file:
        for file_name in sorted(glob.glob(os.path.join(input_directory, input_file_name) + '*')):
            with open(file_name, 'rb') as input_file:
                output_file.write(input_file.read())


def main():
    # noinspection SpellCheckingInspection
    log_formatter = logging.Formatter(
        "%(asctime)s [%(module)-15s %(levelname)-8s]     %(message)s",
        style='%'
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    # Parse command-line arguments
    cli_parser = argparse.ArgumentParser(description='Merge split files',
                                         allow_abbrev=False)
    cli_parser.add_argument('--input', '--file-path', '--path',
                            '-i', '-f', '-p',
                            type=str,
                            required=True,
                            help='Input file name (except ` - part n`)')
    cli_parser.add_argument('--output', '--output-file-path', '--out',
                            '-o',
                            type=str,
                            default=None,
                            required=False,
                            help='Output file name (defaults to input file name)')
    cli_arguments = vars(cli_parser.parse_args())
    input_file_path = cli_arguments['input']
    output_file_path = cli_arguments['output']
    merge_files(input_file_path=input_file_path,
                output_file_path=output_file_path)


if __name__ == '__main__':
    main()
