import bentoml
import os
import tempfile
from neural_synth_modeler.main import infer_params


# Define your model serving class
@bentoml.service(
    resources={"cpu": 2, "memory": "4Gi"},  # Adjust based on your model's needs
    traffic={"timeout": 60},  # Adjust timeout as necessary
)
class NeuralSynthModelerService:
    def __init__(self) -> None:
        pass  # No model loading here; handled by infer_params

    @bentoml.api
    def predict(self, audio_file: bentoml.io.File) -> dict:
        """
        Receives an audio file, runs inference using infer_params, and returns synthesizer parameters.
        This matches the main.py usage pattern - returns filename and eval_dict.
        
        Args:
            audio_file: Input audio file (WAV format recommended)
            
        Returns:
            dict: Contains output_params_file path and eval_dict
        """
        # 1. Save uploaded file to a temporary location
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                # Read the uploaded file content
                file_content = audio_file.read()
                tmp.write(file_content)
                tmp_path = tmp.name
        except Exception as e:
            return {"error": f"Error saving uploaded audio: {str(e)}"}

        # 2. Run inference using infer_params
        try:
            output_params_file, eval_dict = infer_params(
                input_audio_name=tmp_path,
                synth_name="vital",
                enable_eval=True
            )
            
            # Clean up the temp input file
            os.remove(tmp_path)
            
        except Exception as e:
            # Clean up temp file even if inference fails
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return {"error": f"Error during model inference: {str(e)}"}

        # 3. Return the result as JSON - matches main.py return format
        return {
            "output_params_file": output_params_file,
            "eval_dict": eval_dict
        }

