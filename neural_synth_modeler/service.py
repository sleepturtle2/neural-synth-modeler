from pathlib import Path
from typing import Annotated
from bentoml.validators import ContentType
import bentoml
from neural_synth_modeler.main import infer_params
import logging
import requests
import tempfile
import os

@bentoml.service(
    resources={"cpu": 2, "memory": "4Gi"},
    traffic={"timeout": 60},
)
class NeuralSynthModelerService:
    @bentoml.api
    def predict(
        self,
        audio: Annotated[bytes, ContentType("audio/wav")],
    ) -> Annotated[bytes, ContentType("application/octet-stream")]:
        try:
            # Create a temporary file to save the audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio)
                temp_file_path = temp_file.name
            
            logging.info(f"Saved audio data to temporary file: {temp_file_path}")
            
            # Process the audio file
            output_params_file, eval_dict = infer_params(
                input_audio_name=temp_file_path,
                synth_name="vital",
                enable_eval=True
            )
            
            # Read the output file
            with open(output_params_file, 'rb') as f:
                output_data = f.read()
            
            # Clean up temporary files
            try:
                os.unlink(temp_file_path)
                if os.path.exists(output_params_file):
                    os.unlink(output_params_file)
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup temporary files: {cleanup_error}")
            
            logging.info(f"Successfully processed audio -> {output_params_file}")
            return output_data
            
        except Exception as e:
            logging.exception("Error during model inference")
            raise
