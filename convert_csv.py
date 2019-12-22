import csv
import html
import os
import shutil
from typing import Dict, List

EXTRACTED_DIR_PATH = "extracted_articles"
DEFAULT_TASK_NAME = "ArgumentationStrategyTask"


def extract_ids_and_text(filename: str):
    """Open the CSV file and read out a dictionary of article IDs and text."""

    with open(filename, newline='', encoding='utf-8') as csv_file:
        # Read as CSV
        reader = csv.reader(csv_file, delimiter='\t')
        headers = next(reader)

        # Validate that headers are as expected
        validate_headers(headers)

        # Create dictionary of article IDs and text
        articles_by_id = dict()
        for row in reader:
            id = row[0]
            article_text = row[6]
            articles_by_id[id] = article_text

        return articles_by_id


def validate_headers(headers: List[str]):
    """Validate that the headers (and thus the rest of the CSV) is in the
    expected format, so that we can extract data by column index later."""

    if not (len(headers) == 8
            and headers[0] == 'Article ID'
            and headers[6] == 'Article Text'):
        raise ValueError('CSV is not in expected format. Found headers: '
                         + str(headers))


def unescape(raw_articles: Dict[str, str]):
    """Unescape HTML characters such as newlines as &#10;.
    Also trim leading and trailing whitespace.
    """

    return {article_id: html.unescape(text).strip()
            for article_id, text in raw_articles.items()}


def write_each_to_xml(articles_by_id: Dict[str, str], task_name: str):
    """Write dictionary of articles to MAE-compatible XML files for a given
    MAE task name."""

    # Create directory for articles
    success_creating = create_directory(EXTRACTED_DIR_PATH)
    if not success_creating:
        return

    # Write each file
    for article_id, article_text in articles_by_id.items():
        write_to_xml(article_id, article_text, task_name, EXTRACTED_DIR_PATH)


def create_directory(dir_path: str):
    """Create the directory or ask to overwrite it if it already exists."""

    try:
        # Create directory
        os.makedirs(dir_path)
    except FileExistsError:
        # Directory already exists
        should_replace = input('Directory \'{}\' already exists. '
                               'Would you like to replace its contents? [y/N] '
                               .format(dir_path))
        if should_replace.lower() == 'y':
            # Delete folder and contents
            shutil.rmtree(dir_path)
            # Create new, empty directory
            os.makedirs(dir_path)
        else:
            print('Aborting CSV conversion.')
            return False

    return True


def write_to_xml(article_id: str, article_text: str, task_name: str,
                 dir_path: str):
    """Write a given article to a MAE-compatible XML file for a given MAE task
    name, at the location 'dir_path/article_id.xml'."""

    file_path = dir_path + '/' + article_id + '.xml'
    file = open(file_path, 'w+', encoding='utf-8')
    file.write(to_task_xml(article_text, task_name))


def to_task_xml(article_text: str, task_name: str):
    """Assemble the XML required for a MAE task."""

    xml = '<?xml version="1.0" encoding="UTF-8" ?>\n\n'  # Start with schema
    xml += '<' + task_name + '>\n'  # Open task
    xml += '<TEXT>'  # Open text
    xml += '<![CDATA['  # Open CDATA block
    xml += article_text  # Article text goes inside CDATA
    xml += ']]>'  # Close CDATA
    xml += '</TEXT>\n'  # Close text
    xml += '<TAGS>\n</TAGS>\n'  # Add empty tags (since not annotated yet)
    xml += '</' + task_name + '>\n'  # Close task

    return xml


def get_task_name():
    """Check with the user that the default task name is correct, or ask for
    a new one."""

    task_name = DEFAULT_TASK_NAME

    task_name_correct = input(
        'Is \'{}\' the correct task name for the scheme? [Y/n] '
            .format(task_name))
    if task_name_correct.lower() == 'n':
        task_name = input('Please type the new task name: ')

    print('Using task name: \'{}\''.format(task_name))
    return task_name


if __name__ == '__main__':
    raw_articles = extract_ids_and_text('unannotated.csv')
    articles = unescape(raw_articles)

    correct_task_name = get_task_name()
    write_each_to_xml(articles, correct_task_name)
