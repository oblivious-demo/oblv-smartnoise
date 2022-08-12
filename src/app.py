from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, UploadFile, File

from models import DPModelSelect, EXPORT_TYPES
from config import Settings

app = FastAPI()
runtime_args = Settings()

# select the model specified by the config
app.model = DPModelSelect[runtime_args.method](
    parties=runtime_args.party_names, 
    epsilon=runtime_args.epsilon, 
    params=runtime_args.params
    )
app.method = runtime_args.method
app.model_status = "awaiting data"

def train_model():
    try:
        if app.model.train_ready():
            app.model_status = "training"
            app.model.train()
            app.model_status = "trained"

    except Exception as error:
        app.model_status = "failed"
        raise error


@app.post("/upload_data")
async def post_data(
    file: UploadFile = File(...),
    x_oblv_user_name: str = Header(None)
    ):

    try:
        app.model.set_data(file, x_oblv_user_name)

    except ValueError as error:
        raise HTTPException(status_code=error.args[1], detail=str(error.args[0]))

    return {"message": "Upload completed"}

@app.get("/confirm_data")
def confirm_data(
    background_tasks: BackgroundTasks,
    x_oblv_user_name: str = Header(None)
):
    try:
        app.model.confirm_data(x_oblv_user_name)
        background_tasks.add_task(train_model)
    except ValueError as error:
        raise HTTPException(status_code=error.args[1], detail=str(error.args[0]))

    return {"message": "Data confirmed"}

@app.get("/formats")
def get_formats():
    return EXPORT_TYPES.__args__


@app.get("/samples")
async def get_samples(
    format: str = "csv",
    num_samples: int = 1000,
    ):

    try:
        result = app.model.export(format=format, num_samples=num_samples)
    except ValueError as error:
        raise HTTPException(status_code=error.args[1], detail=str(error.args[0]))

    return result

@app.get("/columns")
async def get_columns(
    party: str = "mine", # allowed values ["mine", "theirs"]
    x_oblv_user_name: str = Header(None)
    ):

    try:
        return app.model.columns(requester=x_oblv_user_name, party=party)
    except ValueError as error:
        raise HTTPException(status_code=error.args[1], detail=str(error.args[0]))

@app.get("/details")
async def get_details():
    return {
        "method" : app.method,
        "epsilon": app.model.epsilon,
        "params" : app.model.params,
        "party_names": list(app.model.parties.keys())
    }

@app.get("/model_status")
async def get_details():
    return f"Model status: {app.model_status}"