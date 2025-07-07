from pathlib import Path
from typing import Annotated
from bentoml.validators import ContentType
import bentoml
from neural_synth_modeler.main import infer_params
import logging
import requests

@bentoml.service(
    resources={"cpu": 2, "memory": "4Gi"},
    traffic={"timeout": 60},
)
class NeuralSynthModelerService:
    @bentoml.api
    def predict(
        self,
        audio: Annotated[Path, ContentType("audio/wav")],
    ) -> Annotated[Path, ContentType("application/octet-stream")]:
        try:
            output_params_file, eval_dict = infer_params(
                input_audio_name=str(audio),
                synth_name="vital",
                enable_eval=True
            )
        except Exception as e:
            logging.exception("Error during model inference")
            raise

        logging.info(f"Successfully processed {audio} -> {output_params_file}")
        return Path(output_params_file)
