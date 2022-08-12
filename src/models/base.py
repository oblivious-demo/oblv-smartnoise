# This is just a template for the synthetic data class
from abc import ABC, abstractmethod
from typing import List, Dict,  Literal

import pandas as pd
from fastapi import File
from fastapi.responses import StreamingResponse
import pandas as pd
import numpy as np

import io

# global: supported export formats
EXPORT_TYPES = Literal["csv", "json"]
PARTY_SELECTOR = Literal["mine", "theirs"]
DEFAULT_UPLOAD = {
        "uploaded_data": None,
        "confirmed": False,
        "catagorical_mapping": None
    }

class SDModel(ABC):

    def __init__(self, parties: List[str], epsilon: float, params: Dict):
        self._fitted = False
        self.params = params
        self.epsilon = epsilon

        if len(parties) == 2:
            self.parties = {
                parties[0]: DEFAULT_UPLOAD.copy(),
                parties[1]: DEFAULT_UPLOAD.copy()
            }
        else:
            raise ValueError(f"There must only be 2 parties. Found {len(parties)}", 500)
        
    # SD Model must have a positive flow epsilon:
    @property
    def epsilon(self):
        return self._epsilon

    @epsilon.setter
    def epsilon(self, epsilon):
        if isinstance(epsilon, (int, float)) and (epsilon > 0):
            self._epsilon = epsilon
        else:
            raise ValueError(f"Epsilon must be of type float and be strictly positive.", 500)


    def columns(self, requester: str, party: PARTY_SELECTOR) -> List[str]:
        # user is the party requesting the columns
        # party is either "mine" or "theirs" depending whos columns are needed
        
        if requester not in self.parties.keys():
            raise ValueError(f"{requester} is not a party.", 401)
        
        them = list(self.parties.keys())
        them.remove(requester)
        party_name = requester if party=="mine" else them[0]
        
        if self.parties[party_name]["confirmed"]:
            # format for easy renering in JS tables

            # format rows
            rows = [ list(v) for v in list(self.parties[party_name]["catagorical_mapping"].values()) ]
            rows_maxlen = max([len(r) for r in rows])
            # fill with ''
            rows_balanced = [ r + ['']*(rows_maxlen - len(r)) for r in rows]
            # transpose the list
            rows_T = list(map(list, zip(*rows_balanced)))

            return {
                "user": party_name,
                "columns": self.parties[party_name]["uploaded_data"].columns.tolist(),
                "rows": rows_T
            }
        else:
            raise ValueError(f"{party_name} has not uploaded and confirmed their data yet.", 500)

    # SD Model must be able to set data from each party
    def set_data(self, csv: File, party: str):
        if party in self.parties.keys():
            if self.parties[party]["confirmed"]:
                raise ValueError(f"This person has already uploaded their data.", 409)
        else:
            raise ValueError(f"{party} is not a valid party in {self.parties.keys()}.", 401)

        # now create a temperary dataframe
        tmp_df = pd.read_csv(csv.file)
        
        if "id" not in tmp_df.columns.values:
            raise ValueError(f"id must be a column in the csv file uploaded.", 400)
        else:
            if tmp_df["id"].is_unique:
                tmp_df.set_index("id", inplace=True)
            else:
                raise ValueError(f"All values in the id column must be unique. This is important for the differential privacy budget.", 400)

        # add username as prefix
        tmp_df = tmp_df.add_prefix(party+"_")

        # create a column mapping from catagorical to ints [1,2,3,4....]
        col_mapping = {}
        for cat in tmp_df.columns:
            if cat != "id":
                col_mapping[cat] = dict([
                    (category, code) for code, category in enumerate(tmp_df[cat].astype('category').cat.categories)
                    ])

                tmp_df[cat] = tmp_df[cat].map(lambda x: col_mapping[cat][x])

        self.parties[party]["catagorical_mapping"] = col_mapping

        self.parties[party]["uploaded_data"] = tmp_df

    def train(self):
        self.join_data()
        self.fit()
        self._fitted = True

    def train_ready(self):
        if list(self.parties.values())[0]["confirmed"] &\
            list(self.parties.values())[1]["confirmed"]:
                return True
        return False

    def confirm_data(self, party: str):
        if party not in self.parties.keys():
            raise ValueError(f"{party} is not a valid party in {self.parties.keys()}.", 401)

        self.parties[party]["confirmed"] = True

    def join_data(self) -> None:
        values = [list(self.parties.values())[0]["uploaded_data"], \
            list(self.parties.values())[1]["uploaded_data"]]
        
        joint_data = values[0].join(
            values[1],
            how="inner"
        )
        
        self._joint_data = joint_data

    @abstractmethod  # Decorator to define an abstract method
    def fit(self) -> None:
        # the data to fit is in self._joint_data and is a dataframe
        # the function should have no return, only fit any internals eg self._model etc as required for sampling
        pass

    @abstractmethod  # Decorator to define an abstract method
    def sample(self, num_samples: int) -> pd.DataFrame:
        # you should use the model etc trained in the self.fit() to sample `num_samples` samples and return a dataframe
        pass

    def to_DataFrame(self, arr: np.array) -> pd.DataFrame:
        samples_df = pd.DataFrame(arr, columns=self._joint_data.columns)
        keys = list(self.parties.keys())

        for col in samples_df.columns:
            if col[0:len(keys[0])] == keys[0]:
                client_name = keys[0]
            else:
                client_name = keys[1]

            inv_map = [k for k, v in self.parties[client_name]["catagorical_mapping"][col].items()]

            samples_df[col] = samples_df[col].map(lambda x: inv_map[x])

        return samples_df


    def export(self, num_samples: int, format: EXPORT_TYPES) -> StreamingResponse:
        
        if num_samples <= 0:
            raise ValueError(f"Cannot sample less than 0.", 400)
        elif not self._fitted:
            raise ValueError(f"Model is not yet fit to data. Please wait until the data has been uploaded and model fitted.", 400)
        
        stream = io.StringIO()

        if format == "csv":
            # CSV creation
            self.sample(num_samples).to_csv(stream, index = False)
            response = StreamingResponse(
                iter([stream.getvalue()]),
                media_type="text/csv"
            )
            response.headers["Content-Disposition"] = "attachment; filename=synthetic_data.csv"

        elif format == "json":
            # JSON creation
            self.sample(num_samples).to_json(stream, index = False)
            response = StreamingResponse(
                iter([stream.getvalue()]),
                media_type="application/json"
            )
            response.headers["Content-Disposition"] = "attachment; filename=synthetic_data.json"

        else:
            return {
                "error": True,
                "message":"This format is not supported. Please try {EXPORT_TYPES}"
            }

        return response
        