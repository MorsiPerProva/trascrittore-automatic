import gradio as gr
import whisper
import os
import subprocess
from datetime import datetime

# Carica il modello Whisper
model = whisper.load_model("medium")

# Funzione per convertire in MP3 (supporta M4A, MP4, ecc.)
def convert_to_mp3(file_path):
    output_path = "converted_audio.mp3"
    command = ["ffmpeg", "-i", file_path, "-q:a", "0", "-map", "a", output_path, "-y"]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

# Funzione per trascrivere con avanzamento realistico
def trascrivi(file_audio):
    try:
        file_path = file_audio.name if hasattr(file_audio, "name") else file_audio

        # Controlla il formato e converti se necessario
        if not file_path.endswith(".mp3"):
            file_path = convert_to_mp3(file_path)

        # Calcola la durata del file audio
        command = ["ffmpeg", "-i", file_path, "-hide_banner"]
        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = result.stderr.decode()
        duration_str = [line for line in output.split("\n") if "Duration" in line]
        if duration_str:
            duration_str = duration_str[0].split(",")[0].split("Duration:")[1].strip()
            hours, minutes, seconds = map(float, duration_str.split(":"))
            total_duration = hours * 3600 + minutes * 60 + seconds
        else:
            total_duration = 0

        if total_duration == 0:
            return "Errore: Impossibile determinare la durata del file audio."

        # Inizia la trascrizione
        start_time = datetime.now()
        result = model.transcribe(file_path, language="it")
        elapsed_time = (datetime.now() - start_time).total_seconds()
        progress = min(int((elapsed_time / total_duration) * 100), 100)

        trascrizione = result["text"]

        # Salva la trascrizione in un file
        output_file = "trascrizione.txt"
        with open(output_file, "w") as f:
            f.write(trascrizione)

        # Rimuovi file temporanei
        if os.path.exists("converted_audio.mp3"):
            os.remove("converted_audio.mp3")

        return f"Trascrizione completata! Scarica il file qui: {output_file}"
    except Exception as e:
        return f"Errore: {str(e)}"

# Configura l'interfaccia Gradio
with gr.Blocks() as demo:
    gr.Markdown("## Trascrittore Audio con Avanzamento Reale e Avvio Automatico")

    file_input = gr.File(label="Carica un file audio/video", file_types=None)

    status_output = gr.Textbox(label="Stato")
    file_output = gr.File(label="Scarica Trascrizione")

    file_input.change(
        trascrivi,
        inputs=file_input,
        outputs=[status_output]
    )

demo.launch(server_name="0.0.0.0", server_port=8080)