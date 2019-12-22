import csv

import math
from bs4 import BeautifulSoup
from collections import Counter
from os import listdir, path
from typing import Dict, Optional

annotators = ['Micaela', 'Shantina', 'Danyi']


class GoldStandardLine:
    MAX_DIFF = 3

    def __init__(self, filename, sentence, start, end):
        self.sentence: str = sentence.strip()

        self.file_id = filename[:3]
        self.start_index: int = int(start)
        self.end_index: int = int(end)

        self.tags_by_annotator: Dict[str, Optional[str]] = \
            {annotator: None for annotator in annotators}
        self.gold_tag: Optional[str] = None

    def get_sentence_id(self):
        return self.file_id + '_' + str(self.start_index) + '-' + str(self.end_index)

    def is_same(self, other_line):
        # Take absolute value
        start_diff = math.fabs(self.start_index - other_line.start_index)

        return self.sentence == other_line.sentence \
               and start_diff < GoldStandardLine.MAX_DIFF

    def begins(self, other_line):
        # Take absolute value
        start_diff = math.fabs(self.start_index - other_line.start_index)

        return other_line.sentence.startswith(self.sentence) \
               and start_diff < GoldStandardLine.MAX_DIFF

    def set_gold_from_majority(self):
        tag_counts = Counter(self.tags_by_annotator.values())
        majority_tag = tag_counts.most_common(1)[0][0]
        if tag_counts[majority_tag] >= 2 and majority_tag is not None:
            self.gold_tag = majority_tag

    def to_array(self):
        arr = [self.get_sentence_id(), self.sentence]
        arr.extend(str(self.tags_by_annotator[annotator])
                   for annotator in annotators)
        arr.append(str(self.gold_tag))
        return arr

    @staticmethod
    def array_headers():
        """Returns headers for array produced by to_array"""
        headers = ['ID', 'Sentence']
        headers.extend(annotator for annotator in annotators)
        headers.append('Gold')
        return headers


class GoldStandardCsvCreator:
    def __init__(self):
        self.gold_standard_lines: Dict[str, GoldStandardLine] = {}
        self.annotated_dir = 'annotated_articles'
        self.csv_name = 'gold_standard.csv'

    def get_sorted_gold_standard_lines(self):
        return sorted(self.gold_standard_lines.values(),
                      key=lambda line: (line.file_id, line.start_index))

    def calculate_gold_standard(self):
        self.collect_annotations()
        for line in self.gold_standard_lines.values():
            line.set_gold_from_majority()

    def collect_annotations(self):
        for annotator in annotators:
            annotator_path = self.annotated_dir + '/' + annotator
            for filename in listdir(annotator_path):
                with open(path.join(annotator_path, filename), encoding='utf-8') as file:
                    xml = BeautifulSoup(file, 'xml')
                    tags = xml.ArgumentationStrategyTask.TAGS

                    # Find all child tags that have a name
                    # (i.e. everything except strings)
                    for tag in tags.find_all(True, recursive=False):
                        lines = self.get_gold_standard_lines(filename, tag)

                        # Set annotation by this annotator
                        for line in lines:
                            line.tags_by_annotator[annotator] = tag.name

    def get_gold_standard_lines(self, filename, tag):
        """ Get lines to update (and add to dictionary if not there).
        Should be just one, but may be multiple if the
        annotator accidentally grouped multiple sentences
        """

        # Use attrs because text is a method on the Tag class already
        start_and_end = tag.attrs['spans'].split('~')
        # Create a line object
        line = GoldStandardLine(filename, tag.attrs['text'], start_and_end[0],
                                start_and_end[1])

        # Try to find existing line(s) with fuzzy match
        matching_lines = self.find_matching_lines(line)
        if matching_lines is not None:
            return matching_lines
        else:
            # Add to dictionary and return new line
            self.gold_standard_lines[line.get_sentence_id()] = line
            return [line]

    def find_matching_line(self, line: GoldStandardLine):
        for existing_line in self.gold_standard_lines.values():
            if existing_line.is_same(line):
                return existing_line
        return None

    def find_matching_lines(self, line: GoldStandardLine):
        # Try to match it to a single line
        single_match = self.find_matching_line(line)
        if single_match is not None:
            return [single_match]

        # Maybe it should be multiple lines
        for existing_line in self.gold_standard_lines.values():
            if existing_line.begins(line):
                existing_sentence_end = len(existing_line.sentence)
                second_sentence = line.sentence[existing_sentence_end:]
                if len(second_sentence) == 1:
                    # Looks like the original sentence was missing punctuation
                    # so update it and return that
                    self.update_line(existing_line, line)

                    return [existing_line]

                # Otherwise try to find second sentence
                second_start = line.start_index + existing_sentence_end
                second_line = GoldStandardLine(line.file_id, second_sentence,
                                               second_start, line.end_index)
                matches = self.find_matching_lines(second_line)
                if matches is not None:
                    return [existing_line] + matches
        return None

    def update_line(self, existing_line, new_line):
        # Store the ID before making changes
        prev_id = existing_line.get_sentence_id()

        # Update the sentence
        existing_line.sentence = new_line.sentence
        existing_line.start_index = new_line.start_index
        existing_line.end_index = new_line.end_index

        # ID has changed, so fix dictionary
        del self.gold_standard_lines[prev_id]
        new_id = existing_line.get_sentence_id()
        self.gold_standard_lines[new_id] = existing_line

    def write_to_csv(self):
        with open(self.csv_name, 'w', newline='', encoding='utf-8') as csv_file:
            csvwriter = csv.writer(csv_file)

            csvwriter.writerow(GoldStandardLine.array_headers())
            csvwriter.writerows(line.to_array()
                                for line in self.get_sorted_gold_standard_lines())


if __name__ == '__main__':
    csv_creator = GoldStandardCsvCreator()
    csv_creator.calculate_gold_standard()

    csv_creator.write_to_csv()
