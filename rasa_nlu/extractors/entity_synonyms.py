from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from builtins import range
import io
import json
import os
import warnings

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Text

from rasa_nlu.components import Component
from rasa_nlu.training_data import TrainingData


class EntitySynonymMapper(Component):
    name = "ner_synonyms"

    context_provides = {
        "process": ["entities"],
    }

    output_provides = ["entities"]

    def __init__(self, synonyms=None):
        # type: (Optional[Dict[Text, Text]]) -> None
        self.synonyms = synonyms if synonyms else {}

    def train(self, training_data):
        # type: (TrainingData) -> None

        for key, value in list(training_data.entity_synonyms.items()):
            self.add_entities_if_synonyms(key, value)

        for example in training_data.entity_examples:
            for entity in example["entities"]:
                entity_val = example["text"][entity["start"]:entity["end"]]
                self.add_entities_if_synonyms(entity_val, entity.get("value"))

    def process(self, entities):
        # type: (List[Dict[Text, Any]]) -> Dict[Text, Any]

        updated_entities = entities[:]
        self.replace_synonyms(updated_entities)

        return {
            "entities": updated_entities
        }

    def persist(self, model_dir):
        # type: (Text) -> Dict[Text, Any]

        if self.synonyms:
            entity_synonyms_file = os.path.join(model_dir, "entity_synonyms.json")
            with io.open(entity_synonyms_file, 'w') as f:
                f.write(str(json.dumps(self.synonyms)))
            return {"entity_synonyms": "entity_synonyms.json"}
        else:
            return {"entity_synonyms": None}

    @classmethod
    def load(cls, model_dir, entity_synonyms):
        # type: (Text, Text) -> EntitySynonymMapper

        if model_dir and entity_synonyms:
            entity_synonyms_file = os.path.join(model_dir, entity_synonyms)
            if os.path.isfile(entity_synonyms_file):
                with io.open(entity_synonyms_file, encoding='utf-8') as f:
                    synonyms = json.loads(f.read())
                return EntitySynonymMapper(synonyms)
            else:
                warnings.warn("Failed to load synonyms file from '{}'".format(entity_synonyms_file))
        return EntitySynonymMapper()

    def replace_synonyms(self, entities):
        for i in range(len(entities)):
            entity_value = entities[i]["value"]
            if entity_value.lower() in self.synonyms:
                entities[i]["value"] = self.synonyms[entity_value.lower()]

    def add_entities_if_synonyms(self, entity_a, entity_b):
        if entity_b is not None:
            original = entity_a.lower() if type(entity_a) == str else str(entity_a)
            replacement = entity_b.lower() if type(entity_b) == str else str(entity_b)

            if original != replacement:
                self.synonyms[original] = replacement
