"""
This is the MWEMSynthesizer synthasizer from OpenDP SmartNoise.
Source: https://github.com/opendp/smartnoise-sdk/tree/main/synth

Copyright: Oblivious Software Ltd, 2022.
"""

from .base import SDModel
from typing import Dict, List

from pydantic import BaseModel, ValidationError, validator
import pandas as pd

# the opendp smartnoise synth data package
from snsynth.mst import MSTSynthesizer
import json

class MTSParams(BaseModel):
    # args and defaults from:
    # https://github.com/opendp/smartnoise-sdk/blob/main/synth/snsynth/mwem.py

    delta: float = 1e-9
    

class MTS(SDModel):

    def __init__(self, parties: List[str], epsilon: float, params: dict):
        super().__init__(parties, epsilon, params)

    def fit(self) -> None:
        # the data to fit is in self._joint_data and is a dataframe
        # the function should have no return, only fit any internals 
        # eg self._model etc as required for sampling

        cols = {
            **list(self.parties.values())[0]["catagorical_mapping"], 
            **list(self.parties.values())[1]["catagorical_mapping"]
            }
        cols_len = {k: len(v) for k, v in cols.items()}
        with open('data_meta.json', 'w') as f:
            json.dump(cols_len, f)

        Domains = {
            "data_meta": "data_meta.json"
        }
        
        self._model = MSTSynthesizer(domains_dict=Domains, 
                           domain='data_meta',
                           epsilon=self.epsilon, 
                           **self.params)

        #self._model.fit(self._joint_data.to_numpy())
        self._model.fit(self._joint_data)

    def sample(self, num_samples: int) -> pd.DataFrame:
        # you should use the model etc trained in the self.fit() to 
        # sample `num_samples` samples and return a dataframe.

        samples = self._model.sample(num_samples)

        # use self.to_DataFrame(arr: np.array) to return to original 
        # catagories and column labels.
        return self.to_DataFrame(samples)